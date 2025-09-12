'use client'

import { useState, useCallback } from 'react'
import { TreeView } from '@/components/tree/tree-view'
import { TreeToolbar } from '@/components/tree/tree-toolbar'
import { useInfrastructureStore } from '@/store/use-infrastructure-store'
import { TreeNode as TreeNodeType, BacnetConfig } from '@/types/infrastructure'
import { DraggedPoint } from '@/store/slices/flow-slice'
import { Button } from '@/components/ui/button'
import { Plus, RefreshCw } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { LogicNodesSection } from '@/components/sidebar/logic-nodes-section'
import { ControlFlowSection } from '@/components/sidebar/control-flow-section'
import { CommandNodesSection } from '@/components/sidebar/command-nodes-section'

export function ControllersTreeContainer() {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [newControllerIp, setNewControllerIp] = useState('')
  const [searchValue, setSearchValue] = useState('')

  // Infrastructure store
  const {
    supervisors,
    selectedPointId,
    toggleNode,
    selectPoint,
    expandAll,
    collapseAll,
    getTreeData,
    addController,
    discoverPoints,
  } = useInfrastructureStore()

  // Get tree data
  const treeData = getTreeData()

  // Filter tree data based on search
  const filteredTreeData = searchValue
    ? filterTreeNodes(treeData, searchValue.toLowerCase())
    : treeData

  const handleDragStart = useCallback(
    (e: React.DragEvent, node: TreeNodeType) => {
      if (node.type === 'point' && node.data) {
        const draggedPoint: DraggedPoint = {
          type: 'bacnet-point',
          config: node.data as BacnetConfig,
          draggedFrom: 'controllers-tree',
        }

        e.dataTransfer.effectAllowed = 'copy'
        e.dataTransfer.setData('application/json', JSON.stringify(draggedPoint))
      }
    },
    []
  )

  const handleAddController = useCallback(() => {
    if (!newControllerIp) return

    // Get first supervisor (default)
    const firstSupervisor = Array.from(supervisors.values())[0]
    if (firstSupervisor) {
      addController(firstSupervisor.id, newControllerIp)
      setNewControllerIp('')
      setIsAddDialogOpen(false)
    }
  }, [newControllerIp, supervisors, addController])

  const handleRefreshAll = useCallback(async () => {
    // Refresh all controllers
    for (const supervisor of supervisors.values()) {
      for (const controller of supervisor.controllers) {
        await discoverPoints(supervisor.id, controller.id)
      }
    }
  }, [supervisors, discoverPoints])

  const handleContainerClick = useCallback(() => {
    selectPoint(null) // Clear selection when clicking empty areas
  }, [selectPoint])

  return (
    <div
      className="flex flex-col h-full min-h-0 overflow-y-auto"
      onClick={handleContainerClick}
    >
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="text-sm font-semibold">Controllers</h3>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setIsAddDialogOpen(true)}
            title="Add Controller"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleRefreshAll}
            title="Refresh All"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <TreeToolbar
        onExpandAll={expandAll}
        onCollapseAll={collapseAll}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        showSearch={true}
      />

      <TreeView
        nodes={filteredTreeData}
        selectedNodeId={selectedPointId}
        onToggle={toggleNode}
        onSelect={selectPoint}
        isDraggable={true}
        onDragStart={handleDragStart}
        className="flex-1"
      />

      <LogicNodesSection />
      <ControlFlowSection />
      <CommandNodesSection />

      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Controller</DialogTitle>
            <DialogDescription>
              Enter the IP address of the BACnet controller to add.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="ip-address" className="text-right">
                IP Address
              </Label>
              <Input
                id="ip-address"
                value={newControllerIp}
                onChange={(e) => setNewControllerIp(e.target.value)}
                placeholder="192.168.1.100"
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="submit"
              onClick={handleAddController}
              disabled={!newControllerIp}
            >
              Add Controller
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Helper function to filter tree nodes
function filterTreeNodes(
  nodes: TreeNodeType[],
  searchTerm: string
): TreeNodeType[] {
  return nodes.reduce<TreeNodeType[]>((filtered, node) => {
    const nodeMatches =
      node.label.toLowerCase().includes(searchTerm) ||
      node.sublabel?.toLowerCase().includes(searchTerm)

    let filteredChildren: TreeNodeType[] = []
    if (node.children) {
      filteredChildren = filterTreeNodes(node.children, searchTerm)
    }

    if (nodeMatches || filteredChildren.length > 0) {
      filtered.push({
        ...node,
        children: filteredChildren,
        isExpanded: filteredChildren.length > 0, // Auto-expand if has matching children
      })
    }

    return filtered
  }, [])
}
