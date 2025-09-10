'use client'

import { ChevronRight, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TreeNode as TreeNodeType } from '@/types/infrastructure'

interface TreeNodeProps {
  node: TreeNodeType
  onToggle: (nodeId: string) => void
  onSelect?: (nodeId: string | null) => void
  isSelected?: boolean
  isDraggable?: boolean
  onDragStart?: (e: React.DragEvent, node: TreeNodeType) => void
}

export function TreeNode({
  node,
  onToggle,
  onSelect,
  isSelected = false,
  isDraggable = false,
  onDragStart,
}: TreeNodeProps) {
  const handleClick = (e: React.MouseEvent) => {
    if (node.hasChildren) {
      e.stopPropagation()
      onToggle(node.id)
    }
  }

  const handleSelect = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onSelect) {
      if (node.type === 'point') {
        onSelect(node.id)
      } else {
        // Clear selection when clicking non-point nodes
        onSelect(null)
      }
    }
  }

  const handleDragStart = (e: React.DragEvent) => {
    if (isDraggable && onDragStart && node.type === 'point') {
      onDragStart(e, node)
    } else {
      e.preventDefault()
    }
  }

  const paddingLeft = node.depth * 16

  return (
    <div
      className={cn(
        'flex items-center gap-1 py-1.5 px-2 hover:bg-accent/50 cursor-pointer select-none',
        isSelected && 'bg-accent',
        node.type === 'point' && 'hover:bg-accent'
      )}
      style={{ paddingLeft: `${paddingLeft}px` }}
      onClick={handleSelect}
      draggable={isDraggable && node.type === 'point'}
      onDragStart={handleDragStart}
    >
      {node.hasChildren && (
        <button
          onClick={handleClick}
          className="p-0.5 hover:bg-accent-foreground/10 rounded"
        >
          {node.isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </button>
      )}

      {!node.hasChildren && <span className="w-4" />}

      <span className="text-sm mr-1">{node.icon}</span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-sm font-medium truncate',
              node.type === 'point' && 'text-foreground/90'
            )}
          >
            {node.label}
          </span>
        </div>

        {node.sublabel && (
          <span className="text-xs text-muted-foreground truncate block">
            {node.sublabel}
          </span>
        )}
      </div>
    </div>
  )
}
