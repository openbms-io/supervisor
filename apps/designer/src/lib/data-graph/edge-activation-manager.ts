import { Node, Edge } from '@xyflow/react'
import {
  EdgeData,
  NodeCategory,
  NodeDirection,
  DataNode,
} from '@/types/infrastructure'
import { NodeDataRecord } from './data-graph'

export class EdgeActivationManager {
  private edgesMap: Map<string, Edge<EdgeData>>
  private nodesMap: Map<string, Node<NodeDataRecord>>

  constructor(
    edgesMap: Map<string, Edge<EdgeData>>,
    nodesMap: Map<string, Node<NodeDataRecord>>
  ) {
    this.edgesMap = edgesMap
    this.nodesMap = nodesMap
  }

  /**
   * Initialize edge states based on source node categories
   * Control flow edges start inactive, others start active
   */
  initializeEdgeStates(): void {
    for (const edge of this.edgesMap.values()) {
      if (!edge.data) continue

      const sourceNode = this.nodesMap.get(edge.source)
      if (!sourceNode?.data) continue

      // Control flow outputs start inactive until activated
      const isControlFlow =
        (sourceNode.data as DataNode).category === NodeCategory.CONTROL_FLOW
      edge.data.isActive = !isControlFlow
    }
  }

  /**
   * Activate specific output edges from a control flow node
   */
  activateOutputs(nodeId: string, activeHandles: string[]): void {
    const edges = this.getOutgoingEdges(nodeId)

    for (const edge of edges) {
      if (!edge.data) continue

      // Activate if handle matches
      const handle = edge.sourceHandle || 'default'
      edge.data.isActive = activeHandles.includes(handle)
    }
  }

  /**
   * Check if a node is reachable (has active path or is source)
   */
  isNodeReachable(nodeId: string): boolean {
    const node = this.nodesMap.get(nodeId)
    if (!node?.data) return false

    // Check if it's a source node
    if (this.isSourceNode(node.data)) return true

    // Check incoming edges for active paths
    const hasActiveIncomingEdge = this.hasActiveIncomingEdge(nodeId)
    return hasActiveIncomingEdge
  }

  private isSourceNode(nodeData: NodeDataRecord): boolean {
    const dataNode = nodeData as DataNode

    // Constants are always sources
    if (dataNode.type === 'constant') return true

    // BACnet inputs are sources
    if (
      dataNode.category === NodeCategory.BACNET &&
      dataNode.direction === NodeDirection.OUTPUT
    ) {
      return true
    }

    // Nodes with no incoming edges are sources
    const nodeId = dataNode.id
    const incomingCount = this.getIncomingEdges(nodeId).length
    return incomingCount === 0
  }

  private hasActiveIncomingEdge(nodeId: string): boolean {
    const incomingEdges = this.getIncomingEdges(nodeId)

    // No incoming edges means it's a source
    if (incomingEdges.length === 0) return true

    // Check if at least one incoming edge is active
    return incomingEdges.some((edge) => {
      // No data means active by default
      if (!edge.data) return true
      // Check isActive (undefined means active)
      return edge.data.isActive !== false
    })
  }

  private getOutgoingEdges(nodeId: string): Edge<EdgeData>[] {
    const edges: Edge<EdgeData>[] = []
    for (const edge of this.edgesMap.values()) {
      if (edge.source === nodeId) {
        edges.push(edge)
      }
    }
    return edges
  }

  getIncomingEdges(nodeId: string): Edge<EdgeData>[] {
    const edges: Edge<EdgeData>[] = []
    for (const edge of this.edgesMap.values()) {
      if (edge.target === nodeId) {
        edges.push(edge)
      }
    }
    return edges
  }

  /**
   * Reset all edges to inactive at start of execution
   */
  resetAllEdges(): void {
    for (const edge of this.edgesMap.values()) {
      if (edge.data) {
        edge.data.isActive = false
      }
    }
  }

  /**
   * Activate all output edges from a node (for regular nodes)
   */
  activateAllOutputHandleEdges(nodeId: string): void {
    const edges = this.getOutgoingEdges(nodeId)
    for (const edge of edges) {
      if (edge.data) {
        edge.data.isActive = true
      }
    }
  }

  /**
   * Activate specific output handle edges (for control flow nodes)
   */
  activateSpecificOutputHandleEdges(
    nodeId: string,
    activeHandles: string[]
  ): void {
    const edges = this.getOutgoingEdges(nodeId)
    for (const edge of edges) {
      if (edge.data) {
        const handle = edge.sourceHandle || 'default'
        edge.data.isActive = activeHandles.includes(handle)
      }
    }
  }

  /**
   * Get activation state for visualization
   */
  getEdgeVisualizationState(edgeId: string): {
    isActive: boolean
    isControlFlow: boolean
  } {
    const edge = this.edgesMap.get(edgeId)
    if (!edge?.data) return { isActive: true, isControlFlow: false }

    const sourceNode = this.nodesMap.get(edge.source)
    const nodeData = sourceNode?.data as DataNode
    const isControlFlow = nodeData?.category === NodeCategory.CONTROL_FLOW

    return {
      isActive: edge.data.isActive !== false,
      isControlFlow,
    }
  }
}
