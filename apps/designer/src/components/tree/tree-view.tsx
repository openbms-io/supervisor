'use client'

import { TreeNode } from './tree-node'
import { TreeNode as TreeNodeType } from '@/types/infrastructure'
import { ScrollArea } from '@/components/ui/scroll-area'

interface TreeViewProps {
  nodes: TreeNodeType[]
  selectedNodeId?: string | null
  onToggle: (nodeId: string) => void
  onSelect?: (nodeId: string | null) => void
  isDraggable?: boolean
  onDragStart?: (e: React.DragEvent, node: TreeNodeType) => void
  className?: string
}

export function TreeView({
  nodes,
  selectedNodeId,
  onToggle,
  onSelect,
  isDraggable = false,
  onDragStart,
  className,
}: TreeViewProps) {
  const renderNodes = (nodes: TreeNodeType[]): React.ReactNode => {
    return nodes.map((node) => (
      <div key={node.id}>
        <TreeNode
          node={node}
          onToggle={onToggle}
          onSelect={onSelect}
          isSelected={selectedNodeId === node.id}
          isDraggable={isDraggable}
          onDragStart={onDragStart}
        />

        {node.isExpanded && node.children && node.children.length > 0 && (
          <div>{renderNodes(node.children)}</div>
        )}
      </div>
    ))
  }

  return (
    <ScrollArea className={className}>
      <div className="py-2">{renderNodes(nodes)}</div>
    </ScrollArea>
  )
}
