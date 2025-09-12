import { Node, Edge } from '@xyflow/react'
import { EdgeData, DataNode } from '@/types/infrastructure'
import { NodeDataRecord } from '@/lib/data-graph/data-graph'
import { Message } from './types'
import { v4 as uuidv4 } from 'uuid'

export class MessageRouter {
  // No stored state - pure functions only

  /**
   * Get outgoing edges from a node
   * Pure function - no side effects
   */
  private getOutgoingEdges(
    nodeId: string,
    edges: Edge<EdgeData>[]
  ): Edge<EdgeData>[] {
    return edges.filter((edge) => edge.source === nodeId)
  }

  /**
   * Get incoming edges to a node
   * Pure function - no side effects
   */
  private getIncomingEdges(
    nodeId: string,
    edges: Edge<EdgeData>[]
  ): Edge<EdgeData>[] {
    return edges.filter((edge) => edge.target === nodeId)
  }

  /**
   * Filter edges by source handle
   * Pure function
   */
  private filterBySourceHandle(
    edges: Edge<EdgeData>[],
    handle: string
  ): Edge<EdgeData>[] {
    return edges.filter((edge) => (edge.sourceHandle || 'output') === handle)
  }

  /**
   * Filter active edges
   * Pure function
   */
  private filterActiveEdges(edges: Edge<EdgeData>[]): Edge<EdgeData>[] {
    return edges.filter((edge) => edge.data?.isActive !== false)
  }

  /**
   * Get node by ID
   * Pure function
   */
  private getNodeById(
    nodeId: string,
    nodes: Node<NodeDataRecord>[]
  ): Node<NodeDataRecord> | undefined {
    return nodes.find((node) => node.id === nodeId)
  }

  /**
   * Ensure message has required fields
   * Pure function - returns new message if needed
   */
  private ensureMessageFields(message: Message): Message {
    if (!message._msgid || !message.timestamp) {
      return {
        ...message,
        _msgid: message._msgid || uuidv4(),
        timestamp: message.timestamp || Date.now(),
      }
    }
    return message
  }

  /**
   * Main routing function
   * Pure function - takes all dependencies as parameters
   */
  async routeMessage(
    message: Message,
    fromNodeId: string,
    handle: string,
    nodes: Node<NodeDataRecord>[],
    edges: Edge<EdgeData>[]
  ): Promise<number> {
    console.log(
      `📤 Routing from [${fromNodeId}] handle '${handle}':`,
      message.payload
    )

    const validMessage = this.ensureMessageFields(message)

    // Get edges from this handle
    const outgoingEdges = this.getOutgoingEdges(fromNodeId, edges)
    const handleEdges = this.filterBySourceHandle(outgoingEdges, handle)
    const activeEdges = this.filterActiveEdges(handleEdges)

    let deliveredCount = 0

    // Route to each target
    for (const edge of activeEdges) {
      const targetNode = this.getNodeById(edge.target, nodes)
      if (!targetNode) continue

      const targetNodeData = targetNode.data as DataNode
      const targetHandle = edge.targetHandle || 'input'

      console.log(`  📬 → [${edge.target}] handle '${targetHandle}'`)

      // All DataNodes implement receive
      await targetNodeData.receive(validMessage, targetHandle, fromNodeId)
      deliveredCount++
    }

    console.log(
      `✅ Delivered to ${deliveredCount}/${activeEdges.length} targets`
    )
    return deliveredCount
  }

  /**
   * Find nodes with no incoming edges
   * Pure function
   */
  findSourceNodes(
    nodes: Node<NodeDataRecord>[],
    edges: Edge<EdgeData>[]
  ): string[] {
    const nodeIds: string[] = []

    for (const node of nodes) {
      const incomingEdges = this.getIncomingEdges(node.id, edges)
      if (incomingEdges.length === 0) {
        nodeIds.push(node.id)
      }
    }

    return nodeIds
  }

  /**
   * Check for cycles using DFS
   * Pure function
   */
  hasCycles(nodes: Node<NodeDataRecord>[], edges: Edge<EdgeData>[]): boolean {
    const adjacencyList = this.buildAdjacencyList(nodes, edges)
    const visited = new Set<string>()
    const recursionStack = new Set<string>()

    for (const node of nodes) {
      if (!visited.has(node.id)) {
        if (
          this.hasCyclesDFS(node.id, visited, recursionStack, adjacencyList)
        ) {
          return true
        }
      }
    }

    return false
  }

  /**
   * Build adjacency list from edges
   * Pure function
   */
  private buildAdjacencyList(
    nodes: Node<NodeDataRecord>[],
    edges: Edge<EdgeData>[]
  ): Map<string, Set<string>> {
    const adjacencyList = new Map<string, Set<string>>()

    // Initialize all nodes
    for (const node of nodes) {
      adjacencyList.set(node.id, new Set())
    }

    // Build from edges
    for (const edge of edges) {
      const sourceSet = adjacencyList.get(edge.source)
      if (sourceSet) {
        sourceSet.add(edge.target)
      }
    }

    return adjacencyList
  }

  /**
   * DFS helper for cycle detection
   * Pure recursive function
   */
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
}
