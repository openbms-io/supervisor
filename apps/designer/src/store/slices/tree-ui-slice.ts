// External libraries
import { StateCreator } from 'zustand'

// Internal absolute imports
import {
  TreeNode,
  PointGroup,
  BacnetObjectType,
  BacnetConfig,
} from '@/types/infrastructure'

// Relative imports
import { InfrastructureSlice } from './infrastructure-slice'

export interface TreeUISlice {
  // UI State only
  expandedNodes: Set<string>
  selectedPointId: string | null

  // Actions
  toggleNode: (nodeId: string) => void
  selectPoint: (pointId: string | null) => void
  expandAll: () => void
  collapseAll: () => void

  // Computed from Infrastructure
  getTreeData: () => TreeNode[]
}

export const createTreeUISlice: StateCreator<
  InfrastructureSlice & TreeUISlice,
  [],
  [],
  TreeUISlice
> = (set, get) => ({
  expandedNodes: new Set(),
  selectedPointId: null,

  toggleNode: (nodeId) => {
    set((state) => {
      const expandedNodes = new Set(state.expandedNodes)
      if (expandedNodes.has(nodeId)) {
        expandedNodes.delete(nodeId)
      } else {
        expandedNodes.add(nodeId)
      }
      return { expandedNodes }
    })
  },

  selectPoint: (pointId) => {
    set({ selectedPointId: pointId })
  },

  expandAll: () => {
    const { supervisors } = get()
    const allNodeIds = new Set<string>()

    supervisors.forEach((supervisor) => {
      allNodeIds.add(supervisor.id)
      supervisor.controllers.forEach((controller) => {
        allNodeIds.add(controller.id)
        if (controller.discoveredPoints.length > 0) {
          const types: BacnetObjectType[] = [
            'analog-input',
            'analog-output',
            'analog-value',
            'binary-input',
            'binary-output',
            'binary-value',
          ]
          types.forEach((type) => {
            allNodeIds.add(`${controller.id}-${type}`)
          })
        }
      })
    })

    set({ expandedNodes: allNodeIds })
  },

  collapseAll: () => {
    set({ expandedNodes: new Set() })
  },

  getTreeData: () => {
    const { supervisors, expandedNodes } = get()
    const treeNodes: TreeNode[] = []

    supervisors.forEach((supervisor) => {
      const supervisorNode: TreeNode = {
        id: supervisor.id,
        type: 'supervisor',
        label: supervisor.name,
        icon: '🖥️',
        depth: 0,
        hasChildren: supervisor.controllers.length > 0,
        isExpanded: expandedNodes.has(supervisor.id),
        data: supervisor,
        children: [],
      }

      if (supervisorNode.isExpanded) {
        supervisor.controllers.forEach((controller) => {
          const controllerNode: TreeNode = {
            id: controller.id,
            type: 'controller',
            label: controller.name,
            sublabel: `${controller.ipAddress} • ${controller.discoveredPoints.length} points`,
            icon:
              controller.status === 'connected'
                ? '🟢'
                : controller.status === 'discovering'
                  ? '🔄'
                  : '🔴',
            depth: 1,
            hasChildren: controller.discoveredPoints.length > 0,
            isExpanded: expandedNodes.has(controller.id),
            data: controller,
            children: [],
          }

          if (
            controllerNode.isExpanded &&
            controller.discoveredPoints.length > 0
          ) {
            // Group by objectType
            const pointsByType = new Map<BacnetObjectType, BacnetConfig[]>()

            controller.discoveredPoints.forEach((point) => {
              const points = pointsByType.get(point.objectType) || []
              points.push(point)
              pointsByType.set(point.objectType, points)
            })

            // Create groups
            const typeOrder: BacnetObjectType[] = [
              'analog-input',
              'analog-output',
              'analog-value',
              'binary-input',
              'binary-output',
              'binary-value',
            ]

            typeOrder.forEach((objectType) => {
              const points = pointsByType.get(objectType)
              if (!points || points.length === 0) return

              const groupId = `${controller.id}-${objectType}`
              const groupNode: TreeNode = {
                id: groupId,
                type: 'point-group',
                label: getPointGroupLabel({ objectType }),
                sublabel: `${points.length} points`,
                icon: getPointGroupIcon({ objectType }),
                depth: 2,
                hasChildren: true,
                isExpanded: expandedNodes.has(groupId),
                data: {
                  objectType,
                  count: points.length,
                  points,
                } as PointGroup,
                children: [],
              }

              if (groupNode.isExpanded) {
                points.forEach((point) => {
                  const pointNode: TreeNode = {
                    id: point.pointId, // Use deterministic pointId
                    type: 'point',
                    label: point.name,
                    sublabel: formatPointValue({ point }),
                    icon: '•',
                    depth: 3,
                    hasChildren: false,
                    isExpanded: false,
                    data: point,
                  }
                  groupNode.children!.push(pointNode)
                })
              }

              controllerNode.children!.push(groupNode)
            })
          }

          supervisorNode.children!.push(controllerNode)
        })
      }

      treeNodes.push(supervisorNode)
    })

    return treeNodes
  },
})

// Helper functions
function getPointGroupLabel({
  objectType,
}: {
  objectType: BacnetObjectType
}): string {
  const labels: Record<BacnetObjectType, string> = {
    'analog-input': 'Analog Inputs',
    'analog-output': 'Analog Outputs',
    'analog-value': 'Analog Values',
    'binary-input': 'Binary Inputs',
    'binary-output': 'Binary Outputs',
    'binary-value': 'Binary Values',
    'multistate-input': 'Multistate Inputs',
    'multistate-output': 'Multistate Outputs',
    'multistate-value': 'Multistate Values',
  }
  return labels[objectType] || objectType
}

function getPointGroupIcon({
  objectType,
}: {
  objectType: BacnetObjectType
}): string {
  const icons: Record<BacnetObjectType, string> = {
    'analog-input': '📊',
    'analog-output': '🔧',
    'analog-value': '🎯',
    'binary-input': '🔌',
    'binary-output': '💡',
    'binary-value': '⚡',
    'multistate-input': '🔢',
    'multistate-output': '🎛️',
    'multistate-value': '📋',
  }
  return icons[objectType] || '📍'
}

function formatPointValue({ point }: { point: BacnetConfig }): string {
  const value = point.presentValue
  const units = point.units ? ` ${point.units}` : ''

  if (typeof value === 'boolean') {
    return value ? 'ON' : 'OFF'
  }

  if (typeof value === 'number') {
    return `${value.toFixed(1)}${units}`
  }

  return String(value)
}
