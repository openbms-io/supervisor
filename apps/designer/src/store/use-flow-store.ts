import { create } from 'zustand'
import { createFlowSlice, FlowSlice } from './slices/flow-slice'
import { createMQTTSlice, MQTTSlice } from './slices/mqtt-slice'

// Flow store (for canvas execution)
export const useFlowStore = create<FlowSlice & MQTTSlice>()((...a) => ({
  ...createFlowSlice(...a),
  ...createMQTTSlice(...a),
}))
