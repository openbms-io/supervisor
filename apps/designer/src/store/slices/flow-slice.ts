// External libraries
import { StateCreator } from 'zustand'
import { Node, Edge, XYPosition } from '@xyflow/react'

// Internal absolute imports
import { DataGraph } from '@/lib/data-graph/data-graph'
import { BacnetConfig, DataNode } from '@/types/infrastructure'

export interface DraggedPoint {
  type: 'bacnet-point'
  config: BacnetConfig
  draggedFrom: 'controllers-tree'
}

export interface ValidationResult {
  isValid: boolean
  errors: string[]
}

export interface FlowSlice {
  // Single source of truth - DataGraph manages everything
  dataGraph: DataGraph

  // Actions
  addNodeFromInfrastructure: (
    draggedPoint: DraggedPoint,
    position: XYPosition
  ) => void
  removeNode: (nodeId: string) => void
  connectNodes: (sourceId: string, targetId: string) => boolean
  updateNodePosition: (nodeId: string, position: XYPosition) => void

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
  dataGraph: new DataGraph(),

  addNodeFromInfrastructure: async (draggedPoint, position) => {
    const { config } = draggedPoint

    // Create DataNode from BacnetConfig
    const dataNode = await createDataNodeFromBacnetConfig({ config })

    // Add to graph (single source of truth)
    get().dataGraph.addNode(dataNode, position)

    // Trigger re-render
    set((state) => ({ ...state }))
  },

  removeNode: (nodeId) => {
    get().dataGraph.removeNode(nodeId)
    // Trigger re-render
    set((state) => ({ ...state }))
  },

  connectNodes: (sourceId, targetId) => {
    const success = get().dataGraph.addConnection(sourceId, targetId)
    if (success) {
      // Trigger re-render
      set((state) => ({ ...state }))
    }
    return success
  },

  updateNodePosition: (nodeId, position) => {
    get().dataGraph.updateNodePosition(nodeId, position)
    // Trigger re-render
    set((state) => ({ ...state }))
  },

  // Delegated queries
  getNodes: () => get().dataGraph.getReactFlowNodes(),
  getEdges: () => get().dataGraph.getReactFlowEdges(),
  validateConnection: (sourceId, targetId) =>
    get().dataGraph.validateConnection(sourceId, targetId),
  getExecutionOrder: () => get().dataGraph.getExecutionOrderDFS(), // DFS execution
})
