import { StateCreator } from 'zustand'
import {
  Supervisor,
  Controller,
  generateInstanceId,
} from '@/types/infrastructure'
import { discoverBACnetPoints } from '@/lib/mock/bacnet-data'

export interface InfrastructureSlice {
  // Single source of truth - direct references
  supervisors: Map<string, Supervisor>

  // Actions
  initializeWithDefaults: () => void
  addController: (supervisorId: string, ipAddress: string) => void
  removeController: (supervisorId: string, controllerId: string) => void
  discoverPoints: (supervisorId: string, controllerId: string) => Promise<void>

  // Queries
  getSupervisor: (id: string) => Supervisor | undefined
  getController: (
    supervisorId: string,
    controllerId: string
  ) => Controller | undefined
  getAllControllers: () => Controller[]
}

export const createInfrastructureSlice: StateCreator<
  InfrastructureSlice,
  [],
  [],
  InfrastructureSlice
> = (set, get) => ({
  supervisors: new Map(),

  initializeWithDefaults: () => {
    const defaultSupervisorId = generateInstanceId()
    const defaultSupervisor: Supervisor = {
      id: defaultSupervisorId,
      name: 'Default Supervisor',
      status: 'active',
      controllers: [], // Direct array, not IDs
    }

    set({
      supervisors: new Map([[defaultSupervisorId, defaultSupervisor]]),
    })
  },

  addController: (supervisorId, ipAddress) => {
    const controller: Controller = {
      id: generateInstanceId(),
      supervisorId,
      ipAddress,
      name: `Controller ${ipAddress.split('.').pop()}`,
      status: 'disconnected',
      discoveredPoints: [],
      lastDiscovered: undefined,
    }

    set((state) => {
      const supervisors = new Map(state.supervisors)
      const supervisor = supervisors.get(supervisorId)
      if (supervisor) {
        supervisor.controllers = [...supervisor.controllers, controller]
        supervisors.set(supervisorId, { ...supervisor })
      }
      return { supervisors }
    })
  },

  removeController: (supervisorId, controllerId) => {
    set((state) => {
      const supervisors = new Map(state.supervisors)
      const supervisor = supervisors.get(supervisorId)
      if (supervisor) {
        supervisor.controllers = supervisor.controllers.filter(
          (c) => c.id !== controllerId
        )
        supervisors.set(supervisorId, { ...supervisor })
      }
      return { supervisors }
    })
  },

  discoverPoints: async (supervisorId, controllerId) => {
    const supervisor = get().supervisors.get(supervisorId)
    if (!supervisor) return

    const controller = supervisor.controllers.find((c) => c.id === controllerId)
    if (!controller) return

    // Set status to discovering
    set((state) => {
      const supervisors = new Map(state.supervisors)
      const sup = supervisors.get(supervisorId)
      if (sup) {
        const ctrl = sup.controllers.find((c) => c.id === controllerId)
        if (ctrl) {
          ctrl.status = 'discovering'
          supervisors.set(supervisorId, { ...sup })
        }
      }
      return { supervisors }
    })

    // Discover points
    const points = await discoverBACnetPoints(supervisorId, controllerId)

    // Update controller with points
    set((state) => {
      const supervisors = new Map(state.supervisors)
      const sup = supervisors.get(supervisorId)
      if (sup) {
        const ctrl = sup.controllers.find((c) => c.id === controllerId)
        if (ctrl) {
          ctrl.status = 'connected'
          ctrl.discoveredPoints = points
          ctrl.lastDiscovered = new Date()
          supervisors.set(supervisorId, { ...sup })
        }
      }
      return { supervisors }
    })
  },

  getSupervisor: (id) => get().supervisors.get(id),

  getController: (supervisorId, controllerId) => {
    const supervisor = get().supervisors.get(supervisorId)
    return supervisor?.controllers.find((c) => c.id === controllerId)
  },

  getAllControllers: () => {
    const controllers: Controller[] = []
    get().supervisors.forEach((supervisor) => {
      controllers.push(...supervisor.controllers)
    })
    return controllers
  },
})
