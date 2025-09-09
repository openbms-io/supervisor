import {
  DataNode,
  LogicNode,
  ComputeValue,
  NodeCategory,
  BacnetInputOutput,
  EdgeData,
  isBacnetProperty,
  BacnetPropertyKey,
  CalculationInputHandle,
  ComparisonInputHandle,
} from '@/types/infrastructure'
import { Node, Edge } from '@xyflow/react'
import { ConstantNode } from '@/lib/data-nodes/constant-node'
import { BacnetProperties } from '@/types/bacnet-properties'

// Type for React Flow node data
export type NodeDataRecord = DataNode & Record<string, unknown>

/**
 * DataGraph manages the execution logic using DFS traversal.
 * It maintains only two maps as the source of truth, deriving everything else on-demand.
 */
export class DataGraph {
  // Single source of truth - only two maps!
  private nodesMap: Map<string, Node<NodeDataRecord>>
  private edgesMap: Map<string, Edge<EdgeData>>

  constructor() {
    this.nodesMap = new Map()
    this.edgesMap = new Map()
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

  addConnection(
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ): boolean {
    const sourceNode = this.nodesMap.get(sourceId)
    const targetNode = this.nodesMap.get(targetId)

    if (!sourceNode || !targetNode) return false

    const source = sourceNode.data as DataNode
    const target = targetNode.data as DataNode

    if (!source.canConnectWith(target)) return false

    const edgeData = this.createEdgeData(
      source,
      target,
      sourceHandle,
      targetHandle
    )

    const edgeId = `${sourceId}-to-${targetId}`
    const edge: Edge<EdgeData> = {
      id: edgeId,
      source: sourceId,
      target: targetId,
      sourceHandle: sourceHandle || undefined,
      targetHandle: targetHandle || undefined,
      data: edgeData,
      type: 'smoothstep',
    }
    this.edgesMap.set(edge.id, edge)

    return true
  }

  removeConnection(sourceId: string, targetId: string): void {
    this.edgesMap.delete(`${sourceId}-to-${targetId}`)
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
        return logicNode.computedValue

      case NodeCategory.COMMAND:
        return undefined

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

    let expectedHandles: string[] = []

    switch (node.type) {
      case 'calculation':
        const calcHandles: CalculationInputHandle[] = ['input1', 'input2']
        expectedHandles = calcHandles
        break

      case 'comparison':
        const compHandles: ComparisonInputHandle[] = ['value1', 'value2']
        expectedHandles = compHandles
        break

      default:
        return []
    }

    const incomingEdges = this.getIncomingEdges(nodeId)
    const handleValues = new Map<string, ComputeValue>()

    for (const edge of incomingEdges) {
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
  executeGraph(): void {
    const executionOrder = this.getExecutionOrderDFS()

    for (const nodeId of executionOrder) {
      const node = this.getNode(nodeId)
      if (!node) continue

      if (node.category === NodeCategory.LOGIC) {
        const logicNode = node as LogicNode

        if (logicNode.execute) {
          const inputs = this.getNodeInputValues(nodeId)
          logicNode.execute(inputs)
          this.updateNodeData(nodeId)
        }
      }
    }
  }
}
