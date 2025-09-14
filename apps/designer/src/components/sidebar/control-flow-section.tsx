'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, GitBranch, Clock } from 'lucide-react'
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
      type: 'control-flow-node',
      nodeType: item.type,
      label: item.label,
      metadata: item.metadata,
      draggedFrom: 'control-flow-section',
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

export function ControlFlowSection() {
  const [isExpanded, setIsExpanded] = useState(true)

  const controlFlowNodes: DraggableNodeItem[] = [
    {
      type: 'switch',
      label: 'Switch',
      icon: <GitBranch className="w-4 h-4 text-orange-500" />,
      metadata: {
        condition: 'gt',
        threshold: 0,
      },
    },
    {
      type: 'timer',
      label: 'Timer',
      icon: <Clock className="w-4 h-4 text-orange-500" />,
      metadata: {
        duration: 1000,
      },
    },
    // Gate node - not yet implemented
    // {
    //   type: 'gate',
    //   label: 'Gate',
    //   icon: <Filter className="w-4 h-4 text-orange-500" />,
    //   metadata: {},
    // },
    // {
    //   type: 'sequence',
    //   label: 'Sequence',
    //   icon: <Zap className="w-4 h-4 text-orange-500" />,
    //   metadata: {},
    // },
    // {
    //   type: 'delay',
    //   label: 'Delay',
    //   icon: <Clock className="w-4 h-4 text-orange-500" />,
    //   metadata: {
    //     delayMs: 1000,
    //   },
    // },
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
        <span className="font-semibold text-orange-600">Control Flow</span>
      </Button>

      {isExpanded && (
        <div className="px-2 py-1">
          <div className="text-xs text-muted-foreground px-3 py-1 mb-1">
            Route execution paths based on conditions
          </div>
          {controlFlowNodes.map((node) => (
            <DraggableItem key={node.type} item={node} />
          ))}
        </div>
      )}
    </div>
  )
}
