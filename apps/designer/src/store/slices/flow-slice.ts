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
import { DataGraph, type NodeDataRecord } from '@/lib/data-graph/data-graph'
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
import { ScheduleNode, DayOfWeek } from '@/lib/data-nodes/schedule-node'
import { FunctionInput, FunctionNode } from '@/lib/data-nodes/function-node'
import factory from '@/lib/data-nodes/factory'
import { projectsApi } from '@/lib/api/projects'
import {
  serializeWorkflow,
  deserializeWorkflow,
  createNodeFactory,
  type ReactFlowObject,
  type WorkflowMetadata,
  type VersionedWorkflowConfig,
} from '@/lib/workflow/serializer'

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
  | {
      type: 'UPDATE_SCHEDULE_CONFIG'
      nodeId: string
      startTime: string
      endTime: string
      days: DayOfWeek[]
    }
  | {
      type: 'UPDATE_FUNCTION_CONFIG'
      nodeId: string
      code: string
      inputs: FunctionInput[]
      timeout: number
    }

export interface FlowSlice {
  // React Flow state with properly typed nodes
  nodes: Node<NodeData>[]
  edges: Edge<EdgeData>[]

  // DataGraph for business logic
  dataGraph: DataGraph

  // Notification state
  notification: FlowNotification | null

  // Save/load state
  saveStatus: 'saved' | 'saving' | 'error' | 'unsaved'

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

  // Save/load projects
  saveProject: ({ projectId }: { projectId: string }) => Promise<void>
  loadProject: ({ projectId }: { projectId: string }) => Promise<void>
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
  saveStatus: 'unsaved',

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
    } else if (nodeType === 'function') {
      dataNode = factory.createFunctionNode({
        label,
        code:
          (metadata?.code as string) ||
          'function execute(input1) {\n  return input1;\n}',
        inputs: (metadata?.inputs as FunctionInput[]) || [
          { id: 'input1', label: 'Input 1' },
        ],
        timeout: (metadata?.timeout as number) || 1000,
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
    let dataNode: DataNode | null = null

    if (nodeType === 'switch') {
      dataNode = factory.createSwitchNode({
        label,
        condition:
          (metadata?.condition as 'gt' | 'lt' | 'eq' | 'gte' | 'lte') || 'gt',
        threshold: (metadata?.threshold as number) ?? 0,
      })
    } else if (nodeType === 'timer') {
      dataNode = factory.createTimerNode({
        label,
        duration: (metadata?.duration as number) ?? 1000,
      })
    } else if (nodeType === 'schedule') {
      dataNode = factory.createScheduleNode({
        label,
        startTime: metadata?.startTime as string,
        endTime: metadata?.endTime as string,
        days: metadata?.days as DayOfWeek[],
      })
    } else {
      console.warn('Unknown control flow node type:', nodeType)
      return // Exit early if unknown type
    }

    if (dataNode) {
      get().dataGraph.addNode(dataNode, position)

      // Single state update for all control flow nodes
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
          dataNode.setCondition(update.condition)
          dataNode.setThreshold(update.threshold)

          dataGraph.updateNodeData(update.nodeId)

          set({
            nodes: dataGraph.getNodesArray(),
          })

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

      case 'UPDATE_FUNCTION_CONFIG': {
        const dataNode = dataGraph.getNode(update.nodeId)
        if (dataNode && dataNode.type === 'function') {
          // Use public methods instead of direct access
          const functionNode = dataNode as FunctionNode
          functionNode.updateConfig({
            code: update.code,
            inputs: update.inputs,
            timeout: update.timeout,
          })

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
      case 'UPDATE_SCHEDULE_CONFIG': {
        const dataNode = dataGraph.getNode(update.nodeId)
        if (dataNode && dataNode instanceof ScheduleNode) {
          dataNode.setSchedule(update.startTime, update.endTime, update.days)
          dataGraph.updateNodeData(update.nodeId)
          set({
            nodes: dataGraph.getNodesArray(),
          })
        }
        break
      }

      default:
        console.warn('Unknown update type', update)
        break
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

  // Save/load projects
  saveProject: async ({ projectId }: { projectId: string }): Promise<void> => {
    try {
      set({ saveStatus: 'saving' })

      const { nodes, edges } = get()

      // Create ReactFlowObject
      const reactFlowObject: ReactFlowObject = {
        nodes,
        edges,
        viewport: { x: 0, y: 0, zoom: 1 },
      }

      // Serialize workflow
      const metadata: WorkflowMetadata = {
        lastModified: new Date().toISOString(),
      }

      const versionedConfig = serializeWorkflow({ reactFlowObject, metadata })

      console.log('🚀 [FlowStore] Saving project:', versionedConfig)
      // Update project via API (retry handled in API layer)
      await projectsApi.update(projectId, { workflow_config: versionedConfig })

      set({ saveStatus: 'saved' })
      const { showSuccess } = get()
      showSuccess('Saved', 'Workflow saved successfully')
    } catch (error) {
      console.error('Failed to save project:', error)
      set({ saveStatus: 'error' })
      const { showError } = get()
      showError(
        'Save Failed',
        error instanceof Error ? error.message : 'Unable to save workflow'
      )
      throw error
    }
  },

  loadProject: async ({ projectId }: { projectId: string }): Promise<void> => {
    try {
      const project = await projectsApi.get(projectId)

      console.log('🚀 [FlowStore] Loaded project:', project)
      if (project.workflow_config && project.workflow_config !== '{}') {
        const versionedConfig = JSON.parse(
          project.workflow_config
        ) as VersionedWorkflowConfig
        const nodeFactory = createNodeFactory()

        const { nodes, edges } = deserializeWorkflow({
          versionedConfig,
          nodeFactory,
        })

        // Update store and DataGraph
        const dataGraph = get().dataGraph
        dataGraph.setNodesArray(nodes as Node<NodeDataRecord>[])
        dataGraph.setEdgesArray(edges as Edge<EdgeData>[])

        console.log('🚀 [FlowStore] Loaded project:', nodes, edges)
        set({
          nodes: nodes as Node<NodeData>[],
          edges: edges as Edge<EdgeData>[],
          saveStatus: 'saved',
        })
      } else {
        // Empty workflow config - set to default state
        const dataGraph = get().dataGraph
        dataGraph.setNodesArray([])
        dataGraph.setEdgesArray([])

        set({
          nodes: [],
          edges: [],
          saveStatus: 'saved',
        })
      }
    } catch (error) {
      console.error('Failed to load project:', error)
      set({ saveStatus: 'error' })
      throw error
    }
  },
})
