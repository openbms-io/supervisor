'use client'

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Calculator,
  GitCompare,
  Hash,
} from 'lucide-react'
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
      type: 'logic-node',
      nodeType: item.type,
      label: item.label,
      metadata: item.metadata,
      draggedFrom: 'logic-section',
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

export function LogicNodesSection() {
  const [isExpanded, setIsExpanded] = useState(true)

  const calculationNodes: DraggableNodeItem[] = [
    {
      type: 'calculation',
      label: 'Add',
      icon: <Calculator className="w-4 h-4" />,
      metadata: { operation: 'add' },
    },
    {
      type: 'calculation',
      label: 'Subtract',
      icon: <Calculator className="w-4 h-4" />,
      metadata: { operation: 'subtract' },
    },
    {
      type: 'calculation',
      label: 'Multiply',
      icon: <Calculator className="w-4 h-4" />,
      metadata: { operation: 'multiply' },
    },
    {
      type: 'calculation',
      label: 'Divide',
      icon: <Calculator className="w-4 h-4" />,
      metadata: { operation: 'divide' },
    },
    {
      type: 'calculation',
      label: 'Average',
      icon: <Calculator className="w-4 h-4" />,
      metadata: { operation: 'average' },
    },
  ]

  const comparisonNodes: DraggableNodeItem[] = [
    {
      type: 'comparison',
      label: 'Equals',
      icon: <GitCompare className="w-4 h-4" />,
      metadata: { operation: 'equals' },
    },
    {
      type: 'comparison',
      label: 'Greater Than',
      icon: <GitCompare className="w-4 h-4" />,
      metadata: { operation: 'greater' },
    },
    {
      type: 'comparison',
      label: 'Less Than',
      icon: <GitCompare className="w-4 h-4" />,
      metadata: { operation: 'less' },
    },
    {
      type: 'comparison',
      label: 'Greater or Equal',
      icon: <GitCompare className="w-4 h-4" />,
      metadata: { operation: 'greater-equal' },
    },
    {
      type: 'comparison',
      label: 'Less or Equal',
      icon: <GitCompare className="w-4 h-4" />,
      metadata: { operation: 'less-equal' },
    },
  ]

  const otherNodes: DraggableNodeItem[] = [
    {
      type: 'constant',
      label: 'Constant',
      icon: <Hash className="w-4 h-4" />,
      metadata: { value: 0, valueType: 'number' },
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
        <span className="font-semibold">Logic Nodes</span>
      </Button>

      {isExpanded && (
        <div className="px-2 py-1">
          <div className="text-xs text-muted-foreground px-3 py-1">
            Calculations
          </div>
          {calculationNodes.map((node) => (
            <DraggableItem key={`${node.type}-${node.label}`} item={node} />
          ))}

          <div className="text-xs text-muted-foreground px-3 py-1 mt-2">
            Comparisons
          </div>
          {comparisonNodes.map((node) => (
            <DraggableItem key={`${node.type}-${node.label}`} item={node} />
          ))}

          <div className="text-xs text-muted-foreground px-3 py-1 mt-2">
            Others
          </div>
          {otherNodes.map((node) => (
            <DraggableItem key={`${node.type}-${node.label}`} item={node} />
          ))}
        </div>
      )}
    </div>
  )
}
