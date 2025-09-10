import {
  DataNode,
  LogicNode,
  ComputeValue,
  NodeCategory,
  BacnetInputOutput,
  EdgeData,
  isBacnetProperty,
  CommandNode,
  ControlFlowNode,
} from '@/types/infrastructure'
import { EDGE_TYPES } from '@/types/edge-types'
import { NodeData } from '@/types/node-data-types'
import { Node, Edge } from '@xyflow/react'
import { EdgeActivationManager } from './edge-activation-manager'

// Type for React Flow node data - using NodeData from node-data-types
export type NodeDataRecord = NodeData

/**
 * DataGraph manages the execution logic using DFS traversal.
 * It maintains only two maps as the source of truth, deriving everything else on-demand.
 */
export class DataGraph {
  // Single source of truth - only two maps!
  private nodesMap: Map<string, Node<NodeDataRecord>>

  /** Edge Identity
   * 1. Multiple Edges: Can have multiple edges between the same nodes with different handles
   * 2. Clear Identity: Edge IDs clearly show what's connected (source, handle → target, handle)
   * 3. Proper Deletion: Can delete specific handle connections without affecting others
   * 4. Better Debugging: Edge IDs are human-readable and self-documenting
   * 5. Prevents Duplicates: Won't create duplicate edges for the same handle connections
   */
  private edgesMap: Map<string, Edge<EdgeData>>
  private edgeManager: EdgeActivationManager

  constructor() {
    this.nodesMap = new Map()
    this.edgesMap = new Map()
    this.edgeManager = new EdgeActivationManager(this.edgesMap, this.nodesMap)
  }

  getNodesArray(): Node<NodeDataRecord>[] {
    return Array.from(this.nodesMap.values())
  }

  getEdgesArray(): Edge<EdgeData>[] {
    return Array.from(this.edgesMap.values())
  }

  // Setter for React Flow's applyNodeChanges
  setNodesArray(nodes: Node<NodeDataRecord>[]): void {
    this.nodesMap.clear()
    nodes.forEach((node) => {
      this.nodesMap.set(node.id, node)
    })
  }

  // Setter for React Flow's applyEdgeChanges
  setEdgesArray(edges: Edge<EdgeData>[]): void {
    this.edgesMap.clear()
    edges.forEach((edge) => {
      this.edgesMap.set(edge.id, edge as Edge<EdgeData>)
    })
  }

  // Build adjacency list on-demand from edges
  private buildAdjacencyList(): Map<string, Set<string>> {
    const adjacencyList = new Map<string, Set<string>>()

    // Initialize all nodes
    for (const nodeId of this.nodesMap.keys()) {
      adjacencyList.set(nodeId, new Set())
    }

    // Build from edges
    for (const edge of this.edgesMap.values()) {
      const sourceSet = adjacencyList.get(edge.source)
      if (sourceSet) {
        sourceSet.add(edge.target)
      }
    }

    return adjacencyList
  }

  // Build reverse adjacency list on-demand from edges
  private buildReverseAdjacencyList(): Map<string, Set<string>> {
    const reverseAdjacencyList = new Map<string, Set<string>>()

    // Initialize all nodes
    for (const nodeId of this.nodesMap.keys()) {
      reverseAdjacencyList.set(nodeId, new Set())
    }

    // Build from edges
    for (const edge of this.edgesMap.values()) {
      const targetSet = reverseAdjacencyList.get(edge.target)
      if (targetSet) {
        targetSet.add(edge.source)
      }
    }

    return reverseAdjacencyList
  }

  addNode(node: DataNode, position: { x: number; y: number }): void {
    // For nodes without category, use type as-is. For custom nodes, prepend category
    const nodeType = !node.category
      ? node.type
      : `${node.category}.${node.type}`

    const reactFlowNode: Node<NodeDataRecord> = {
      id: node.id,
      type: nodeType,
      position,
      data: node as NodeDataRecord, // Store the entire DataNode
    }
    this.nodesMap.set(node.id, reactFlowNode)
  }

  removeNode(nodeId: string): void {
    // Remove all edges connected to this node
    const edgesToRemove: string[] = []
    for (const [edgeId, edge] of this.edgesMap) {
      if (edge.source === nodeId || edge.target === nodeId) {
        edgesToRemove.push(edgeId)
      }
    }
    edgesToRemove.forEach((id) => this.edgesMap.delete(id))

    // Remove node
    this.nodesMap.delete(nodeId)
  }

  private createEdgeData(
    source: DataNode,
    target: DataNode,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): EdgeData {
    return {
      sourceData: {
        nodeId: source.id,
        nodeCategory: source.category,
        nodeType: source.type,
        handle: sourceHandle || undefined,
      },
      targetData: {
        nodeId: target.id,
        nodeCategory: target.category,
        nodeType: target.type,
        handle: targetHandle || undefined,
      },
    }
  }

  private generateEdgeId(
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): string {
    const source = `${sourceId}:${sourceHandle || '_'}`
    const target = `${targetId}:${targetHandle || '_'}`
    return `${source}->${target}`
  }

  addConnection(
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): boolean {
    const sourceNode = this.nodesMap.get(sourceId)
    const targetNode = this.nodesMap.get(targetId)

    if (!sourceNode || !targetNode) {
      return false
    }

    const source = sourceNode.data as DataNode
    const target = targetNode.data as DataNode

    if (!source.canConnectWith(target)) return false

    const edgeData = this.createEdgeData(
      source,
      target,
      sourceHandle,
      targetHandle
    )

    const edgeId = this.generateEdgeId(
      sourceId,
      targetId,
      sourceHandle,
      targetHandle
    )

    const edge: Edge<EdgeData> = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      sourceHandle: sourceHandle || undefined,
      targetHandle: targetHandle || undefined,
      data: edgeData,
      type: EDGE_TYPES.CONTROL_FLOW, // Use our custom bidirectional-flow edge type
    }

    this.edgesMap.set(edge.id, edge)

    return true
  }

  removeConnection(
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): void {
    const edgeId = this.generateEdgeId(
      sourceId,
      targetId,
      sourceHandle,
      targetHandle
    )
    this.edgesMap.delete(edgeId)
  }

  // Deprecated - use getNodesArray() and getEdgesArray() instead
  getReactFlowNodes(): Node<NodeDataRecord>[] {
    return this.getNodesArray()
  }

  getReactFlowEdges(): Edge<EdgeData>[] {
    return this.getEdgesArray()
  }

  // DFS execution order
  getExecutionOrderDFS(): string[] {
    const adjacencyList = this.buildAdjacencyList()
    const reverseAdjacencyList = this.buildReverseAdjacencyList()
    const visited = new Set<string>()
    const executionOrder: string[] = []

    // Find source nodes (no incoming edges)
    const sourceNodes: string[] = []
    for (const [nodeId, incoming] of reverseAdjacencyList) {
      if (incoming.size === 0) {
        sourceNodes.push(nodeId)
      }
    }

    // DFS from each source node
    for (const nodeId of sourceNodes) {
      if (!visited.has(nodeId)) {
        this.dfsTraversal(nodeId, visited, executionOrder, adjacencyList)
      }
    }

    return executionOrder
  }

  private dfsTraversal(
    nodeId: string,
    visited: Set<string>,
    executionOrder: string[],
    adjacencyList: Map<string, Set<string>>
  ): void {
    visited.add(nodeId)

    // Process current node
    executionOrder.push(nodeId)

    // Visit all neighbors (DFS)
    const neighbors = adjacencyList.get(nodeId) || new Set()
    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        this.dfsTraversal(neighborId, visited, executionOrder, adjacencyList)
      }
    }
  }

  validateConnection(sourceId: string, targetId: string): boolean {
    const sourceNode = this.nodesMap.get(sourceId)
    const targetNode = this.nodesMap.get(targetId)
    if (!sourceNode || !targetNode) return false

    const source = sourceNode.data as DataNode
    const target = targetNode.data as DataNode
    return source.canConnectWith(target)
  }

  getAllNodes(): DataNode[] {
    return Array.from(this.nodesMap.values()).map(
      (node) => node.data as DataNode
    )
  }

  getNode(nodeId: string): DataNode | undefined {
    const node = this.nodesMap.get(nodeId)
    return node ? (node.data as DataNode) : undefined
  }

  updateNodePosition(nodeId: string, position: { x: number; y: number }): void {
    const node = this.nodesMap.get(nodeId)
    if (node) {
      node.position = position
      this.nodesMap.set(nodeId, node)
    }
  }

  // Force React Flow to detect node changes by creating new node object
  updateNodeData(nodeId: string): void {
    const node = this.nodesMap.get(nodeId)
    if (node) {
      // Create new node object to trigger React Flow update
      this.nodesMap.set(nodeId, { ...node })
    }
  }

  // Check if graph has cycles
  hasCycles(): boolean {
    const adjacencyList = this.buildAdjacencyList()
    const visited = new Set<string>()
    const recursionStack = new Set<string>()

    for (const nodeId of this.nodesMap.keys()) {
      if (!visited.has(nodeId)) {
        if (this.hasCyclesDFS(nodeId, visited, recursionStack, adjacencyList)) {
          return true
        }
      }
    }

    return false
  }

  private hasCyclesDFS(
    nodeId: string,
    visited: Set<string>,
    recursionStack: Set<string>,
    adjacencyList: Map<string, Set<string>>
  ): boolean {
    visited.add(nodeId)
    recursionStack.add(nodeId)

    const neighbors = adjacencyList.get(nodeId) || new Set()
    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        if (
          this.hasCyclesDFS(neighborId, visited, recursionStack, adjacencyList)
        ) {
          return true
        }
      } else if (recursionStack.has(neighborId)) {
        return true // Cycle detected
      }
    }

    recursionStack.delete(nodeId)
    return false
  }

  // Get upstream nodes (nodes that feed into this node)
  getUpstreamNodes(nodeId: string): DataNode[] {
    const reverseAdjacencyList = this.buildReverseAdjacencyList()
    const sourceIds = reverseAdjacencyList.get(nodeId) || new Set()
    return Array.from(sourceIds)
      .map((id) => this.getNode(id))
      .filter((node): node is DataNode => node !== undefined)
  }

  // Get downstream nodes (nodes that this node feeds into)
  getDownstreamNodes(nodeId: string): DataNode[] {
    const adjacencyList = this.buildAdjacencyList()
    const targetIds = adjacencyList.get(nodeId) || new Set()
    return Array.from(targetIds)
      .map((id) => this.getNode(id))
      .filter((node): node is DataNode => node !== undefined)
  }

  private getNodeOutputValue(
    node: DataNode,
    handle?: string
  ): ComputeValue | undefined {
    switch (node.category) {
      case NodeCategory.BACNET:
        if (handle && isBacnetProperty(handle)) {
          const bacnetNode = node as BacnetInputOutput
          const value = bacnetNode.discoveredProperties[handle]
          if (typeof value === 'number' || typeof value === 'boolean') {
            return value
          }
        }
        return undefined

      case NodeCategory.LOGIC:
        const logicNode = node as LogicNode
        return logicNode.getValue()

      case NodeCategory.COMMAND:
        // Command nodes pass through their setpoint value
        const commandNode = node as CommandNode
        return commandNode.receivedValue

      case NodeCategory.CONTROL_FLOW:
        // Control flow nodes pass through their input value
        const cfNode = node as ControlFlowNode
        return cfNode.getValue()

      default:
        return undefined
    }
  }

  // Get incoming edges for a node
  private getIncomingEdges(nodeId: string): Edge<EdgeData>[] {
    const edges: Edge<EdgeData>[] = []
    for (const edge of this.edgesMap.values()) {
      if (edge.target === nodeId) {
        edges.push(edge)
      }
    }
    return edges
  }

  private getNodeInputValues(nodeId: string): ComputeValue[] {
    const node = this.getNode(nodeId)
    if (!node) return []

    // Use the node's getInputHandles method if available
    let expectedHandles: string[] = []
    if (
      'getInputHandles' in node &&
      typeof node.getInputHandles === 'function'
    ) {
      expectedHandles = node.getInputHandles() as string[]
    } else {
      return [] // Node has no inputs
    }

    const incomingEdges = this.getIncomingEdges(nodeId)
    const handleValues = new Map<string, ComputeValue>()

    for (const edge of incomingEdges) {
      // Skip inactive edges
      if (edge.data?.isActive === false) continue

      if (!edge.data || !edge.targetHandle) continue

      const sourceNode = this.getNode(edge.data.sourceData.nodeId)
      if (sourceNode) {
        const value = this.getNodeOutputValue(
          sourceNode,
          edge.data.sourceData.handle
        )
        if (value !== undefined) {
          handleValues.set(edge.targetHandle, value)
        }
      }
    }

    return expectedHandles.map((handle) => handleValues.get(handle) ?? 0)
  }

  // Execute all nodes in topological order
  // Reset all computed values to ensure fresh execution
  private resetComputedValues(): void {
    for (const node of this.nodesMap.values()) {
      const dataNode = node.data as DataNode

      // Use proper API instead of direct access
      if ('reset' in dataNode && typeof dataNode.reset === 'function') {
        dataNode.reset()
      }
    }
  }

  executeGraph(): void {
    // Check for cycles before execution
    if (this.hasCycles()) {
      console.error('Graph contains cycles - execution aborted')
      // Let the store handle notifications
      throw new Error('Graph contains cycles')
    }

    const executionOrder = this.getExecutionOrderDFS()

    // Reset all computed values for fresh execution
    this.resetComputedValues()

    // Initialize edge states
    this.edgeManager.initializeEdgeStates()

    for (const nodeId of executionOrder) {
      const node = this.getNode(nodeId)
      if (!node) continue

      // Skip unreachable nodes
      if (!this.edgeManager.isNodeReachable(nodeId)) continue

      const inputs = this.getNodeInputValues(nodeId)

      // Execute based on category using switch statement
      switch (node.category) {
        case NodeCategory.CONTROL_FLOW: {
          const cfNode = node as ControlFlowNode
          cfNode.execute(inputs)

          // Let edge manager handle activation
          const activeHandles = cfNode.getActiveOutputHandles()
          this.edgeManager.activateOutputs(nodeId, [...activeHandles])
          break
        }

        case NodeCategory.LOGIC: {
          const logicNode = node as LogicNode
          if (logicNode.execute) {
            logicNode.execute(inputs)
          }
          break
        }

        case NodeCategory.COMMAND: {
          const commandNode = node as CommandNode
          commandNode.receivedValue = inputs[0]

          // Find connected BACnet nodes
          const downstreamNodes = this.getDownstreamNodes(nodeId)
          for (const target of downstreamNodes) {
            if (target.category === NodeCategory.BACNET) {
              const bacnetNode = target as BacnetInputOutput
              this.executeBacnetWrite(
                bacnetNode,
                commandNode.receivedValue,
                commandNode.priority,
                commandNode.writeMode
              )
            }
          }
          break
        }

        case NodeCategory.BACNET:
          // Data sources, no execution needed
          break

        default: {
          // Exhaustive check
          const _exhaustive: never = node.category
          console.warn('Unknown node category:', _exhaustive)
        }
      }

      this.updateNodeData(nodeId)
    }
  }

  private executeBacnetWrite(
    bacnetNode: BacnetInputOutput,
    value: ComputeValue | undefined,
    priority: number,
    writeMode: 'normal' | 'override' | 'release'
  ): void {
    if (value === undefined) return

    // TODO: In real implementation, this would:
    // 1. Send write command to IoT supervisor
    // 2. IoT supervisor writes to actual BACnet device
    // 3. Device responds with new value
    // 4. discoveredProperties would be updated from device response

    console.log('BACnet Write Command:', {
      pointId: bacnetNode.pointId,
      objectType: bacnetNode.objectType,
      objectId: bacnetNode.objectId,
      value,
      priority,
      writeMode,
    })
  }

  // Check if an edge exists between nodes with specific handles
  hasEdge(
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): boolean {
    const edgeId = this.generateEdgeId(
      sourceId,
      targetId,
      sourceHandle,
      targetHandle
    )
    return this.edgesMap.has(edgeId)
  }

  // Get edge by nodes and handles
  getEdge(
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): Edge<EdgeData> | undefined {
    const edgeId = this.generateEdgeId(
      sourceId,
      targetId,
      sourceHandle,
      targetHandle
    )
    return this.edgesMap.get(edgeId)
  }

  // Get all edges between two nodes regardless of handles
  getEdgesBetween(sourceId: string, targetId: string): Edge<EdgeData>[] {
    const edges: Edge<EdgeData>[] = []
    for (const edge of this.edgesMap.values()) {
      if (edge.source === sourceId && edge.target === targetId) {
        edges.push(edge)
      }
    }
    return edges
  }
}
