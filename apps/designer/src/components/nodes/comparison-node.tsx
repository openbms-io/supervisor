'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CustomHandle } from './custom-handle'
import { useFlowStore } from '@/store/use-flow-store'
import {
  ComputeValue,
  NodeCategory,
  ComparisonInputHandle,
  LogicOutputHandle,
} from '@/types/infrastructure'
import { ComparisonNodeData } from '@/types/node-data-types'

// Stable empty array to prevent infinite loops
const EMPTY_INPUTS: ComputeValue[] = []

export const ComparisonNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as ComparisonNodeData
  const { label, metadata } = typedData

  const INPUT_HANDLES: ComparisonInputHandle[] = ['value1', 'value2']
  const OUTPUT_HANDLE: LogicOutputHandle = 'output'

  // Use separate selectors to avoid infinite loop
  const inputs = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as ComparisonNodeData
      return logicData.inputValues || EMPTY_INPUTS
    }
    return EMPTY_INPUTS
  })

  const result = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as ComparisonNodeData
      return logicData.computedValue
    }
    return undefined
  })

  const operation = metadata?.operation

  const formatValue = (value: ComputeValue | undefined): string => {
    if (value === undefined) return '-'
    if (typeof value === 'number') {
      return isNaN(value) ? 'NaN' : value.toFixed(2)
    }
    return value ? 'true' : 'false'
  }

  const formatOperation = (op: string | undefined): string => {
    switch (op) {
      case 'equals':
        return '='
      case 'greater':
        return '>'
      case 'less':
        return '<'
      case 'greater-equal':
        return '≥'
      case 'less-equal':
        return '≤'
      default:
        return op || 'equals'
    }
  }

  return (
    <Card className="min-w-[200px] border-2 border-purple-500">
      <div className="p-3 space-y-2">
        <div className="text-center">
          <span className="text-sm font-medium">{label}</span>
          <Badge variant="secondary" className="ml-2 text-xs">
            {formatOperation(operation)}
          </Badge>
        </div>

        {/* Input values display */}
        <div className="text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Value 1:</span>
            <span className="font-mono">
              {formatValue((inputs as ComputeValue[])?.[0])}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Value 2:</span>
            <span className="font-mono">
              {formatValue((inputs as ComputeValue[])?.[1])}
            </span>
          </div>
        </div>

        {/* Result display */}
        <div className="border-t pt-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">Result:</span>
            <span
              className={`text-lg font-bold ${
                result ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {formatValue(result as ComputeValue | undefined)}
            </span>
          </div>
        </div>
      </div>

      <CustomHandle
        type="target"
        position={Position.Left}
        id={INPUT_HANDLES[0]}
        style={{ top: '30%' }}
        className="w-3 h-3 bg-purple-500 border-2 border-background"
        connectionCount={1}
      />
      <CustomHandle
        type="target"
        position={Position.Left}
        id={INPUT_HANDLES[1]}
        style={{ top: '70%' }}
        className="w-3 h-3 bg-purple-500 border-2 border-background"
        connectionCount={1}
      />
      <Handle
        type="source"
        position={Position.Right}
        id={OUTPUT_HANDLE}
        className="w-3 h-3 bg-purple-500 border-2 border-background"
      />
    </Card>
  )
})

ComparisonNode.displayName = 'ComparisonNode'
