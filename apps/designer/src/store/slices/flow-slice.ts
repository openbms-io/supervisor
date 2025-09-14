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
import {
  BacnetConfig,
  DataNode,
  EdgeData,
  NodeTypeString,
} from '@/types/infrastructure'
import { NodeData } from '@/types/node-data-types'
import type {
  CalculationOperation,
  ComparisonOperation,
} from '@/lib/data-nodes'
import type { ValueType } from '@/lib/data-nodes/constant-node'
import { ConstantNode } from '@/lib/data-nodes/constant-node'
import { SwitchNode } from '@/lib/data-nodes/switch-node'
import { TimerNode } from '@/lib/data-nodes/timer-node'
import factory from '@/lib/data-nodes/factory'

export interface DraggedPoint {
  type: 'bacnet-point'
  config: BacnetConfig
  draggedFrom: 'controllers-tree'
}

export interface DraggedLogicNode {
  type: 'logic-node'
  nodeType: NodeTypeString
  label: string
  metadata?: Record<string, unknown>
  draggedFrom: 'logic-section'
}

export interface DraggedCommandNode {
  type: 'command-node'
  nodeType: NodeTypeString
  label: string
  metadata?: Record<string, unknown>
  draggedFrom: 'command-section'
}

export interface DraggedControlFlowNode {
  type: 'control-flow-node'
  nodeType: NodeTypeString
  label: string
  metadata?: Record<string, unknown>
  draggedFrom: 'control-flow-section'
}

export interface ValidationResult {
  isValid: boolean
  errors: string[]
}

export interface FlowNotification {
  type: 'success' | 'error' | 'warning'
  title: string
  message: string
}

// Node update actions
export type NodeUpdate =
  | {
      type: 'UPDATE_CONSTANT_VALUE'
      nodeId: string
      value: number | boolean | string
    }
  | { type: 'UPDATE_CONSTANT_TYPE'; nodeId: string; valueType: ValueType }
  | {
      type: 'UPDATE_SWITCH_CONFIG'
      nodeId: string
      condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
      threshold: number
    }
  | {
      type: 'UPDATE_TIMER_DURATION'
      nodeId: string
      duration: number
    }

export interface FlowSlice {
  // React Flow state with properly typed nodes
  nodes: Node<NodeData>[]
  edges: Edge<EdgeData>[]

  // DataGraph for business logic
  dataGraph: DataGraph

  // Notification state
  notification: FlowNotification | null

  // React Flow change handlers
  onNodesChange: (changes: NodeChange[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void

  // Actions
  addNodeFromInfrastructure: (
    draggedPoint: DraggedPoint,
    position: XYPosition
  ) => void
  addLogicNode: (
    nodeType: NodeTypeString,
    label: string,
    position: XYPosition,
    metadata?: Record<string, unknown>
  ) => void
  addCommandNode: (
    nodeType: NodeTypeString,
    label: string,
    position: XYPosition,
    metadata?: Record<string, unknown>
  ) => void
  addControlFlowNode: (
    nodeType: NodeTypeString,
    label: string,
    position: XYPosition,
    metadata?: Record<string, unknown>
  ) => void
  removeNode: (nodeId: string) => void
  connectNodes: (
    sourceId: string,
    targetId: string,
    sourceHandle?: string | null,
    targetHandle?: string | null
  ) => boolean
  updateNodePosition: (nodeId: string, position: XYPosition) => void
  updateNode: (update: NodeUpdate) => void

  // Notification actions
  setNotification: (notification: FlowNotification | null) => void
  clearNotification: () => void
  showError: (title: string, message: string) => void
  showSuccess: (title: string, message: string) => void
  showWarning: (title: string, message: string) => void

  // Queries (delegated to DataGraph)
  getNodes: () => Node[]
  getEdges: () => Edge[]
  validateConnection: (sourceId: string, targetId: string) => boolean

  // Execute graph
  executeWithMessages: () => Promise<void>
}

// This will be imported from factory once we create it
// For now, we'll create a placeholder
async function createDataNodeFromBacnetConfig({
  config,
}: {
  config: BacnetConfig
}): Promise<DataNode> {
  // Placeholder - will be replaced with actual implementation
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
  notification: null,

  onNodesChange: (changes: NodeChange[]) => {
    const currentNodes = get().nodes
    const updatedNodes = applyNodeChanges(
      changes,
      currentNodes
    ) as Node<NodeDataRecord>[]

    get().dataGraph.setNodesArray(updatedNodes)

    set({ nodes: updatedNodes })
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    const currentEdges = get().edges
    const updatedEdges = applyEdgeChanges(
      changes,
      currentEdges
    ) as Edge<EdgeData>[]

    // Update DataGraph with new edges
    get().dataGraph.setEdgesArray(updatedEdges)

    // Update React Flow state
    set({ edges: updatedEdges })
  },

  addNodeFromInfrastructure: async (draggedPoint, position) => {
    const { config } = draggedPoint

    const dataNode = await createDataNodeFromBacnetConfig({ config })

    get().dataGraph.addNode(dataNode, position)

    set({
      nodes: get().dataGraph.getNodesArray(),
      edges: get().dataGraph.getEdgesArray(),
    })
  },

  addLogicNode: async (nodeType, label, position, metadata) => {
    let dataNode: DataNode

    if (nodeType === 'constant') {
      dataNode = factory.createConstantNode({
        label,
        value: (metadata?.value as number | boolean | string) ?? 0,
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

    set({
      nodes: get().dataGraph.getNodesArray(),
      edges: get().dataGraph.getEdgesArray(),
    })
  },

  addCommandNode: async (nodeType, label, position, metadata) => {
    if (nodeType === 'write-setpoint') {
      const dataNode = factory.createWriteSetpointNode({
        label,
        priority: (metadata?.priority as number) ?? 8,
      })
      get().dataGraph.addNode(dataNode, position)

      // Update React Flow state
      set({
        nodes: get().dataGraph.getNodesArray(),
        edges: get().dataGraph.getEdgesArray(),
      })
    }
  },

  addControlFlowNode: async (nodeType, label, position, metadata) => {
    if (nodeType === 'switch') {
      const dataNode = factory.createSwitchNode({
        label,
        condition:
          (metadata?.condition as 'gt' | 'lt' | 'eq' | 'gte' | 'lte') || 'gt',
        threshold: (metadata?.threshold as number) ?? 0,
      })
      get().dataGraph.addNode(dataNode, position)

      // Update React Flow state
      set({
        nodes: get().dataGraph.getNodesArray(),
        edges: get().dataGraph.getEdgesArray(),
      })
    } else if (nodeType === 'timer') {
      const dataNode = factory.createTimerNode({
        label,
        duration: (metadata?.duration as number) ?? 1000,
      })
      get().dataGraph.addNode(dataNode, position)

      // Update React Flow state
      set({
        nodes: get().dataGraph.getNodesArray(),
        edges: get().dataGraph.getEdgesArray(),
      })
    } else {
      console.warn('Unknown control flow node type:', nodeType)
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

  connectNodes: (sourceId, targetId, sourceHandle, targetHandle) => {
    const { dataGraph, showWarning } = get()

    // Check if edge already exists with these handles
    if (dataGraph.hasEdge(sourceId, targetId, sourceHandle, targetHandle)) {
      showWarning(
        'Connection Already Exists',
        'An edge already exists between these nodes with the same handles.'
      )
      return false
    }

    const success = dataGraph.addConnection(
      sourceId,
      targetId,
      sourceHandle,
      targetHandle
    )

    if (success) {
      const newEdges = dataGraph.getEdgesArray()

      // Update React Flow state
      set({
        nodes: dataGraph.getNodesArray(),
        edges: newEdges,
      })

      // Execute graph after new connection
      get().executeWithMessages()
    } else {
      showWarning(
        'Invalid Connection',
        'These nodes cannot be connected. Check node compatibility.'
      )
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

          // Execute graph after type change
          get().executeWithMessages()
        }
        break
      }

      case 'UPDATE_SWITCH_CONFIG': {
        const dataNode = dataGraph.getNode(update.nodeId)
        if (dataNode && dataNode instanceof SwitchNode) {
          // Use encapsulated setters instead of direct mutation
          dataNode.setCondition(update.condition)
          dataNode.setThreshold(update.threshold)

          // Force React Flow to detect the change
          dataGraph.updateNodeData(update.nodeId)

          // Get fresh nodes array
          set({
            nodes: dataGraph.getNodesArray(),
          })

          // Execute graph after configuration change
          get().executeWithMessages()
        }
        break
      }

      case 'UPDATE_TIMER_DURATION': {
        const dataNode = dataGraph.getNode(update.nodeId)
        if (dataNode && dataNode instanceof TimerNode) {
          dataNode.setDuration(update.duration)
          dataGraph.updateNodeData(update.nodeId)
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

  // Notification actions
  setNotification: (notification) => set({ notification }),

  clearNotification: () => set({ notification: null }),

  showError: (title, message) =>
    set({
      notification: { type: 'error', title, message },
    }),

  showSuccess: (title, message) =>
    set({
      notification: { type: 'success', title, message },
    }),

  showWarning: (title, message) =>
    set({
      notification: { type: 'warning', title, message },
    }),

  // Execute graph with message passing
  executeWithMessages: async () => {
    const { dataGraph, showError, showSuccess } = get()

    try {
      console.log('🚀 [FlowStore] Starting message-based execution...')

      // Execute with messages
      await dataGraph.executeWithMessages()

      // Show success notification
      showSuccess(
        '✅ Message Execution Complete',
        'Successfully executed graph using message passing'
      )

      // No need to force UI updates - BacnetNodeUI subscribes to store directly via Zustand
    } catch (error) {
      showError(
        '⚠️ Message Execution Failed',
        error instanceof Error
          ? error.message
          : 'An unknown error occurred during message execution'
      )
    }
  },
})
