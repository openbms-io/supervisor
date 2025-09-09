'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
interface CalculationData {
  label: string
  metadata?: {
    operation?: string
  }
}

export const CalculationNode = memo(({ data }: NodeProps) => {
  const { label } = data as unknown as CalculationData

  return (
    <Card className="min-w-[160px] border-2 border-blue-500">
      <div className="p-3">
        <div className="text-center">
          <span className="text-sm font-medium">{label}</span>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        id="input1"
        style={{ top: '30%' }}
        className="w-3 h-3 bg-blue-500 border-2 border-background"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="input2"
        style={{ top: '70%' }}
        className="w-3 h-3 bg-blue-500 border-2 border-background"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-blue-500 border-2 border-background"
      />
    </Card>
  )
})

CalculationNode.displayName = 'CalculationNode'
