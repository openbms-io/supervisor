import { create } from 'zustand'
import {
  createInfrastructureSlice,
  InfrastructureSlice,
} from './slices/infrastructure-slice'
import { createTreeUISlice, TreeUISlice } from './slices/tree-ui-slice'

// Infrastructure store (for tree view)
type InfrastructureStoreState = InfrastructureSlice & TreeUISlice

export const useInfrastructureStore = create<InfrastructureStoreState>()(
  (...a) => ({
    ...createInfrastructureSlice(...a),
    ...createTreeUISlice(...a),
  })
)

// Initialize with defaults
useInfrastructureStore.getState().initializeWithDefaults()
