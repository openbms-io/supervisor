'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, PenTool } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface DraggableNodeItem {
  type: string
  label: string
  icon: React.ReactNode
  metadata?: Record<string, unknown>
}

function DraggableItem({ item }: { item: DraggableNodeItem }) {
  const handleDragStart = (e: React.DragEvent) => {
    const dragData = {
      type: 'command-node',
      nodeType: item.type,
      label: item.label,
      metadata: item.metadata,
      draggedFrom: 'command-section',
    }
    e.dataTransfer.effectAllowed = 'copy'
    e.dataTransfer.setData('application/json', JSON.stringify(dragData))
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent cursor-move rounded-md"
    >
      {item.icon}
      <span>{item.label}</span>
    </div>
  )
}

export function CommandNodesSection() {
  const [isExpanded, setIsExpanded] = useState(true)

  const commandNodes: DraggableNodeItem[] = [
    {
      type: 'write-setpoint',
      label: 'Write Setpoint',
      icon: <PenTool className="w-4 h-4" />,
      metadata: { propertyName: 'presentValue' },
    },
    {
      type: 'write-setpoint',
      label: 'Write Priority',
      icon: <PenTool className="w-4 h-4" />,
      metadata: { propertyName: 'priorityArray' },
    },
  ]

  return (
    <div className="border-t">
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start px-3 py-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 mr-2" />
        ) : (
          <ChevronRight className="w-4 h-4 mr-2" />
        )}
        <span className="font-semibold">Command Nodes</span>
      </Button>

      {isExpanded && (
        <div className="px-2 py-1">
          {commandNodes.map((node) => (
            <DraggableItem key={`${node.type}-${node.label}`} item={node} />
          ))}
        </div>
      )}
    </div>
  )
}
