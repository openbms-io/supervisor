import { DataNode } from '@/types/infrastructure'
import { Node, Edge } from '@xyflow/react'

// Type for React Flow node data
export type NodeDataRecord = DataNode & Record<string, unknown>

/**
 * DataGraph manages the execution logic using DFS traversal.
 * It is the single source of truth for canvas nodes and edges.
 */
export class DataGraph {
  private adjacencyList: Map<string, Set<string>>
  private reverseAdjacencyList: Map<string, Set<string>>
  private nodeIndex: Map<string, DataNode>

  // React Flow state (single source of truth)
  private reactFlowNodes: Map<string, Node<NodeDataRecord>>
  private reactFlowEdges: Map<string, Edge>

  // Stable array references - never recreated, only mutated
  private nodesArray: Node<NodeDataRecord>[] = []
  private edgesArray: Edge[] = []

  constructor() {
    this.adjacencyList = new Map()
    this.reverseAdjacencyList = new Map()
    this.nodeIndex = new Map()
    this.reactFlowNodes = new Map()
    this.reactFlowEdges = new Map()
  }

  // Sync arrays with Maps - mutate in place for stable references
  private syncArrays(): void {
    // Clear and repopulate nodes array
    this.nodesArray.length = 0
    this.nodesArray.push(...this.reactFlowNodes.values())

    // Clear and repopulate edges array
    this.edgesArray.length = 0
    this.edgesArray.push(...this.reactFlowEdges.values())
  }

  addNode(node: DataNode, position: { x: number; y: number }): void {
    // Add to graph
    this.nodeIndex.set(node.id, node)
    if (!this.adjacencyList.has(node.id)) {
      this.adjacencyList.set(node.id, new Set())
    }
    if (!this.reverseAdjacencyList.has(node.id)) {
      this.reverseAdjacencyList.set(node.id, new Set())
    }

    // Add React Flow node - spread DataNode to satisfy Record<string, unknown>
    const reactFlowNode: Node<NodeDataRecord> = {
      id: node.id,
      type: `bacnet.${node.type}`,
      position,
      data: { ...node },
    }
    this.reactFlowNodes.set(node.id, reactFlowNode)
    this.syncArrays() // Update stable arrays
  }

  removeNode(nodeId: string): void {
    // Remove all connections
    this.adjacencyList.get(nodeId)?.forEach((targetId) => {
      this.reverseAdjacencyList.get(targetId)?.delete(nodeId)
      this.reactFlowEdges.delete(`${nodeId}-to-${targetId}`)
    })

    this.reverseAdjacencyList.get(nodeId)?.forEach((sourceId) => {
      this.adjacencyList.get(sourceId)?.delete(nodeId)
      this.reactFlowEdges.delete(`${sourceId}-to-${nodeId}`)
    })

    // Remove node
    this.nodeIndex.delete(nodeId)
    this.adjacencyList.delete(nodeId)
    this.reverseAdjacencyList.delete(nodeId)
    this.reactFlowNodes.delete(nodeId)
    this.syncArrays() // Update stable arrays
  }

  addConnection(sourceId: string, targetId: string): boolean {
    const source = this.nodeIndex.get(sourceId)
    const target = this.nodeIndex.get(targetId)

    if (!source || !target) return false

    // Business validation
    if (!source.canConnectWith(target)) return false

    // Add to graph
    this.adjacencyList.get(sourceId)?.add(targetId)
    this.reverseAdjacencyList.get(targetId)?.add(sourceId)

    // Add React Flow edge
    const edge: Edge = {
      id: `${sourceId}-to-${targetId}`,
      source: sourceId,
      target: targetId,
      type: 'smoothstep',
    }
    this.reactFlowEdges.set(edge.id, edge)
    this.syncArrays() // Update stable arrays

    return true
  }

  removeConnection(sourceId: string, targetId: string): void {
    this.adjacencyList.get(sourceId)?.delete(targetId)
    this.reverseAdjacencyList.get(targetId)?.delete(sourceId)
    this.reactFlowEdges.delete(`${sourceId}-to-${targetId}`)
    this.syncArrays() // Update stable arrays
  }

  // Get React Flow nodes and edges (for rendering) - return stable references
  getReactFlowNodes(): Node<NodeDataRecord>[] {
    return this.nodesArray
  }

  getReactFlowEdges(): Edge[] {
    return this.edgesArray
  }

  // DFS execution order
  getExecutionOrderDFS(): string[] {
    const visited = new Set<string>()
    const executionOrder: string[] = []

    // Start DFS from source nodes (no incoming edges)
    const sourceNodes = this.getSourceNodes()

    for (const nodeId of sourceNodes) {
      if (!visited.has(nodeId)) {
        this.dfsTraversal(nodeId, visited, executionOrder)
      }
    }

    return executionOrder
  }

  private dfsTraversal(
    nodeId: string,
    visited: Set<string>,
    executionOrder: string[]
  ): void {
    visited.add(nodeId)

    // Process current node
    executionOrder.push(nodeId)

    // Visit all neighbors (DFS)
    const neighbors = this.adjacencyList.get(nodeId) || new Set()
    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        this.dfsTraversal(neighborId, visited, executionOrder)
      }
    }
  }

  private getSourceNodes(): string[] {
    const sources: string[] = []
    for (const [nodeId, incoming] of this.reverseAdjacencyList) {
      if (incoming.size === 0) {
        sources.push(nodeId)
      }
    }
    return sources
  }

  validateConnection(sourceId: string, targetId: string): boolean {
    const source = this.nodeIndex.get(sourceId)
    const target = this.nodeIndex.get(targetId)
    if (!source || !target) return false
    return source.canConnectWith(target)
  }

  getAllNodes(): DataNode[] {
    return Array.from(this.nodeIndex.values())
  }

  getNode(nodeId: string): DataNode | undefined {
    return this.nodeIndex.get(nodeId)
  }

  updateNodePosition(nodeId: string, position: { x: number; y: number }): void {
    const node = this.reactFlowNodes.get(nodeId)
    if (node) {
      node.position = position
      this.reactFlowNodes.set(nodeId, node)
      this.syncArrays() // Update stable arrays
    }
  }

  // Check if graph has cycles
  hasCycles(): boolean {
    const visited = new Set<string>()
    const recursionStack = new Set<string>()

    for (const nodeId of this.nodeIndex.keys()) {
      if (!visited.has(nodeId)) {
        if (this.hasCyclesDFS(nodeId, visited, recursionStack)) {
          return true
        }
      }
    }

    return false
  }

  private hasCyclesDFS(
    nodeId: string,
    visited: Set<string>,
    recursionStack: Set<string>
  ): boolean {
    visited.add(nodeId)
    recursionStack.add(nodeId)

    const neighbors = this.adjacencyList.get(nodeId) || new Set()
    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        if (this.hasCyclesDFS(neighborId, visited, recursionStack)) {
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
    const sourceIds = this.reverseAdjacencyList.get(nodeId) || new Set()
    return Array.from(sourceIds)
      .map((id) => this.nodeIndex.get(id))
      .filter((node): node is DataNode => node !== undefined)
  }

  // Get downstream nodes (nodes that this node feeds into)
  getDownstreamNodes(nodeId: string): DataNode[] {
    const targetIds = this.adjacencyList.get(nodeId) || new Set()
    return Array.from(targetIds)
      .map((id) => this.nodeIndex.get(id))
      .filter((node): node is DataNode => node !== undefined)
  }
}
