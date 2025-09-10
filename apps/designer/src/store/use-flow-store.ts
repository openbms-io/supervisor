import { create } from 'zustand'
import { createFlowSlice, FlowSlice } from './slices/flow-slice'

// Flow store (for canvas execution)
export const useFlowStore = create<FlowSlice>()((...a) => ({
  ...createFlowSlice(...a),
}))
