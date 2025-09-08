'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { GitCompare } from 'lucide-react'
const operationSymbols = {
  equals: '=',
  greater: '>',
  less: '<',
  'greater-equal': '≥',
  'less-equal': '≤',
}

interface ComparisonData {
  label: string
  metadata?: {
    operation?: keyof typeof operationSymbols
  }
}

export const ComparisonNode = memo(({ data }: NodeProps) => {
  const { label, metadata } = data as unknown as ComparisonData
  const operation = metadata?.operation || 'equals'

  return (
    <Card className="min-w-[160px] border-2 border-purple-500">
      <div className="p-3">
        <div className="flex items-center gap-2 mb-2">
          <GitCompare className="w-4 h-4 text-purple-500" />
          <span className="text-sm font-medium">{label}</span>
        </div>

        <div className="flex items-center justify-center">
          <Badge variant="secondary" className="text-lg font-mono">
            {operationSymbols[operation]}
          </Badge>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        id="value1"
        style={{ top: '30%' }}
        className="w-3 h-3 bg-purple-500 border-2 border-background"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="value2"
        style={{ top: '70%' }}
        className="w-3 h-3 bg-purple-500 border-2 border-background"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-purple-500 border-2 border-background"
      />
    </Card>
  )
})

ComparisonNode.displayName = 'ComparisonNode'
