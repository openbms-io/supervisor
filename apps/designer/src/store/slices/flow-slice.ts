// External libraries
import { StateCreator } from 'zustand'
import {
  Node,
  Edge,
  XYPosition,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
} from '@xyflow/react'

// Internal absolute imports
import { DataGraph, NodeDataRecord } from '@/lib/data-graph/data-graph'
import { BacnetConfig, DataNode } from '@/types/infrastructure'
import type {
  CalculationOperation,
  ComparisonOperation,
} from '@/lib/data-nodes'
import type { ValueType } from '@/lib/data-nodes/constant-node'
import { ConstantNode } from '@/lib/data-nodes/constant-node'

export interface DraggedPoint {
  type: 'bacnet-point'
  config: BacnetConfig
  draggedFrom: 'controllers-tree'
}

export interface DraggedLogicNode {
  type: 'logic-node'
  nodeType: string
  label: string
  metadata?: Record<string, unknown>
  draggedFrom: 'logic-section'
}

export interface DraggedCommandNode {
  type: 'command-node'
  nodeType: string
  label: string
  metadata?: Record<string, unknown>
  draggedFrom: 'command-section'
}

export interface ValidationResult {
  isValid: boolean
  errors: string[]
}

// Node update actions
export type NodeUpdate =
  | {
      type: 'UPDATE_CONSTANT_VALUE'
      nodeId: string
      value: number | boolean | string
    }
  | { type: 'UPDATE_CONSTANT_TYPE'; nodeId: string; valueType: ValueType }

export interface FlowSlice {
  // React Flow state
  nodes: Node[]
  edges: Edge[]

  // DataGraph for business logic
  dataGraph: DataGraph

  // React Flow change handlers
  onNodesChange: (changes: NodeChange[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void

  // Actions
  addNodeFromInfrastructure: (
    draggedPoint: DraggedPoint,
    position: XYPosition
  ) => void
  addLogicNode: (
    nodeType: string,
    label: string,
    position: XYPosition,
    metadata?: Record<string, unknown>
  ) => void
  addCommandNode: (
    nodeType: string,
    label: string,
    position: XYPosition,
    metadata?: Record<string, unknown>
  ) => void
  removeNode: (nodeId: string) => void
  connectNodes: (sourceId: string, targetId: string) => boolean
  updateNodePosition: (nodeId: string, position: XYPosition) => void
  updateNode: (update: NodeUpdate) => void

  // Queries (delegated to DataGraph)
  getNodes: () => Node[]
  getEdges: () => Edge[]
  validateConnection: (sourceId: string, targetId: string) => boolean
  getExecutionOrder: () => string[]
}

// This will be imported from factory once we create it
// For now, we'll create a placeholder
async function createDataNodeFromBacnetConfig({
  config,
}: {
  config: BacnetConfig
}): Promise<DataNode> {
  // Placeholder - will be replaced with actual implementation
  const { default: factory } = await import('@/lib/data-nodes/factory')
  return factory.createDataNodeFromBacnetConfig({ config })
}

export const createFlowSlice: StateCreator<FlowSlice, [], [], FlowSlice> = (
  set,
  get
) => ({
  // Initialize state
  nodes: [],
  edges: [],
  dataGraph: new DataGraph(),

  // React Flow change handlers
  onNodesChange: (changes: NodeChange[]) => {
    const currentNodes = get().nodes
    const updatedNodes = applyNodeChanges(
      changes,
      currentNodes
    ) as Node<NodeDataRecord>[]

    // Update DataGraph with new nodes
    get().dataGraph.setNodesArray(updatedNodes)

    // Update React Flow state
    set({ nodes: updatedNodes })
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    const currentEdges = get().edges
    const updatedEdges = applyEdgeChanges(changes, currentEdges)

    // Update DataGraph with new edges
    get().dataGraph.setEdgesArray(updatedEdges)

    // Update React Flow state
    set({ edges: updatedEdges })
  },

  addNodeFromInfrastructure: async (draggedPoint, position) => {
    const { config } = draggedPoint

    // Create DataNode from BacnetConfig
    const dataNode = await createDataNodeFromBacnetConfig({ config })

    // Add to graph (single source of truth)
    get().dataGraph.addNode(dataNode, position)

    // Update React Flow state
    set({
      nodes: get().dataGraph.getNodesArray(),
      edges: get().dataGraph.getEdgesArray(),
    })
  },

  addLogicNode: async (nodeType, label, position, metadata) => {
    const { default: factory } = await import('@/lib/data-nodes/factory')
    let dataNode: DataNode

    if (nodeType === 'constant') {
      dataNode = factory.createConstantNode({
        label,
        value: metadata?.value ?? 0,
        valueType: (metadata?.valueType as ValueType) ?? 'number',
      })
    } else if (nodeType === 'calculation') {
      dataNode = factory.createCalculationNode({
        label,
        operation: (metadata?.operation as CalculationOperation) || 'add',
      })
    } else if (nodeType === 'comparison') {
      dataNode = factory.createComparisonNode({
        label,
        operation: (metadata?.operation as ComparisonOperation) || 'equals',
      })
    } else {
      console.warn('Unknown logic node type:', nodeType)
      return
    }

    get().dataGraph.addNode(dataNode, position)

    // Update React Flow state
    set({
      nodes: get().dataGraph.getNodesArray(),
      edges: get().dataGraph.getEdgesArray(),
    })
  },

  addCommandNode: async (nodeType, label, position, metadata) => {
    const { default: factory } = await import('@/lib/data-nodes/factory')

    if (nodeType === 'write-setpoint') {
      const dataNode = factory.createWriteSetpointNode({
        label,
        targetPointId: metadata?.targetPointId as string,
        propertyName: metadata?.propertyName as string,
      })
      get().dataGraph.addNode(dataNode, position)

      // Update React Flow state
      set({
        nodes: get().dataGraph.getNodesArray(),
        edges: get().dataGraph.getEdgesArray(),
      })
    }
  },

  removeNode: (nodeId) => {
    get().dataGraph.removeNode(nodeId)
    // Update React Flow state
    set({
      nodes: get().dataGraph.getNodesArray(),
      edges: get().dataGraph.getEdgesArray(),
    })
  },

  connectNodes: (sourceId, targetId) => {
    const success = get().dataGraph.addConnection(sourceId, targetId)
    if (success) {
      // Update React Flow state
      set({
        nodes: get().dataGraph.getNodesArray(),
        edges: get().dataGraph.getEdgesArray(),
      })
    }
    return success
  },

  updateNodePosition: (nodeId, position) => {
    get().dataGraph.updateNodePosition(nodeId, position)
    // Update React Flow state
    set({
      nodes: get().dataGraph.getNodesArray(),
      edges: get().dataGraph.getEdgesArray(),
    })
  },

  updateNode: (update) => {
    const dataGraph = get().dataGraph

    switch (update.type) {
      case 'UPDATE_CONSTANT_VALUE': {
        // Get the DataNode from DataGraph
        const dataNode = dataGraph.getNode(update.nodeId)
        if (dataNode && dataNode instanceof ConstantNode) {
          // Update the ConstantNode
          dataNode.setValue(update.value)

          // Force React Flow to detect the change
          dataGraph.updateNodeData(update.nodeId)

          // Get fresh nodes array
          set({
            nodes: dataGraph.getNodesArray(),
          })
        }
        break
      }

      case 'UPDATE_CONSTANT_TYPE': {
        const dataNode = dataGraph.getNode(update.nodeId)
        if (dataNode && dataNode instanceof ConstantNode) {
          // Update the ConstantNode (this also resets the value)
          dataNode.setValueType(update.valueType)

          // Force React Flow to detect the change
          dataGraph.updateNodeData(update.nodeId)

          // Get fresh nodes array
          set({
            nodes: dataGraph.getNodesArray(),
          })
        }
        break
      }

      default:
        // Exhaustive check
        const _exhaustive: never = update
        console.warn('Unknown update type', _exhaustive)
    }
  },

  // Delegated queries
  getNodes: () => get().dataGraph.getNodesArray(),
  getEdges: () => get().dataGraph.getEdgesArray(),
  validateConnection: (sourceId, targetId) =>
    get().dataGraph.validateConnection(sourceId, targetId),
  getExecutionOrder: () => get().dataGraph.getExecutionOrderDFS(), // DFS execution
})
