'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Calculator } from 'lucide-react'
const operationIcons = {
  add: '+',
  subtract: '-',
  multiply: '×',
  divide: '÷',
  average: 'AVG',
}

interface CalculationData {
  label: string
  metadata?: {
    operation?: keyof typeof operationIcons
  }
}

export const CalculationNode = memo(({ data }: NodeProps) => {
  const { label, metadata } = data as unknown as CalculationData
  const operation = metadata?.operation || 'add'

  return (
    <Card className="min-w-[160px] border-2 border-blue-500">
      <div className="p-3">
        <div className="flex items-center gap-2 mb-2">
          <Calculator className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-medium">{label}</span>
        </div>

        <div className="flex items-center justify-center">
          <Badge variant="secondary" className="text-lg font-mono">
            {operationIcons[operation]}
          </Badge>
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
