import { DataNode, EdgeData } from '@/types/infrastructure'
import {
  EDGE_TYPES,
  DEFAULT_INPUT_HANDLE,
  DEFAULT_OUTPUT_HANDLE,
} from '@/types/edge-types'
import { NodeData } from '@/types/node-data-types'
import { Node, Edge } from '@xyflow/react'
import { EdgeActivationManager } from './edge-activation-manager'
import { MessageRouter } from '@/lib/message-system/message-router'
import { Message } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export type NodeDataRecord = NodeData

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
  private messageRouter: MessageRouter

  constructor() {
    this.nodesMap = new Map()
    this.edgesMap = new Map()
    this.edgeManager = new EdgeActivationManager(this.edgesMap, this.nodesMap)
    this.messageRouter = new MessageRouter()
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

  addNode(node: DataNode, position: { x: number; y: number }): void {
    // Inject routing callback if node supports messages
    if (
      'setSendCallback' in node &&
      typeof node.setSendCallback === 'function'
    ) {
      const callback = async (
        message: Message,
        nodeId: string,
        handle: string
      ) => {
        // Activate only the edges from this specific handle
        this.edgeManager.activateSpecificOutputEdges(nodeId, handle)

        // Get fresh arrays each time for pure router
        const nodes = this.getNodesArray()
        const edges = this.getEdgesArray()

        // Use pure router function
        await this.messageRouter.routeMessage(
          message,
          nodeId,
          handle,
          nodes,
          edges
        )
      }

      ;(
        node as DataNode & {
          setSendCallback: (
            cb: (
              message: Message,
              nodeId: string,
              handle: string
            ) => Promise<void>
          ) => void
        }
      ).setSendCallback(callback)
    } else {
      console.log('Node does not support messages. setSendCallback')
    }

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
    // Get node before removal for cleanup
    const node = this.nodesMap.get(nodeId)
    if (node) {
      const dataNode = node.data as DataNode
      // Call reset if available to cleanup timers/intervals
      if ('reset' in dataNode && typeof dataNode.reset === 'function') {
        dataNode.reset()
      }
    }

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
    const source = `${sourceId}:${sourceHandle || DEFAULT_OUTPUT_HANDLE}`
    const target = `${targetId}:${targetHandle || DEFAULT_INPUT_HANDLE}`
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

  // Message-based execution using pure router
  async executeWithMessages(): Promise<void> {
    console.log('🚀 Starting message-based execution')

    const nodes = this.getNodesArray()
    const edges = this.getEdgesArray()

    // Use pure router to check for cycles
    if (this.messageRouter.hasCycles(nodes, edges)) {
      console.error('Graph contains cycles - execution aborted')
      throw new Error('Graph contains cycles')
    }

    // Reset nodes
    this.resetComputedValues()

    // Reset edge activation
    this.edgeManager.resetAllEdges()

    // Find source nodes using pure router
    const sourceNodeIds = this.messageRouter.findSourceNodes(nodes, edges)
    console.log('🎯 Found source nodes:', sourceNodeIds)

    // Activate edges from source nodes
    for (const nodeId of sourceNodeIds) {
      this.edgeManager.activateAllOutputHandleEdges(nodeId)
    }

    // Start the chain reaction by triggering source nodes
    for (const nodeId of sourceNodeIds) {
      const node = this.nodesMap.get(nodeId)
      if (node) {
        const dataNode = node.data as DataNode
        console.log(`⚡ Triggering source node: ${nodeId}`)

        // Send trigger message to start the flow
        await dataNode.receive(
          {
            _msgid: uuidv4(),
            timestamp: Date.now(),
            payload: true,
            metadata: { trigger: true },
          },
          DEFAULT_INPUT_HANDLE,
          'system'
        )
      }
    }

    console.log('✨ Message-based execution completed')
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
}
