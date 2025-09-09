'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
interface ComparisonData {
  label: string
  metadata?: {
    operation?: string
  }
}

export const ComparisonNode = memo(({ data }: NodeProps) => {
  const { label } = data as unknown as ComparisonData

  return (
    <Card className="min-w-[160px] border-2 border-purple-500">
      <div className="p-3">
        <div className="text-center">
          <span className="text-sm font-medium">{label}</span>
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
