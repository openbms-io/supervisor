'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CustomHandle } from './custom-handle'
import {
  CommandInputHandle,
  CommandOutputHandle,
  ComputeValue,
} from '@/types/infrastructure'
import { WriteSetpointNodeData } from '@/types/node-data-types'
import { useFlowStore } from '@/store/use-flow-store'

export const WriteSetpointNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as WriteSetpointNodeData
  const { label, priority } = typedData

  const INPUT_HANDLE: CommandInputHandle = 'setpoint'
  const OUTPUT_HANDLE: CommandOutputHandle = 'output'

  // Subscribe to inputValue via useFlowStore for reactive updates
  const inputValue = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    const nodeData = node?.data
    return nodeData?.inputValue as ComputeValue | undefined
  })

  const formatValue = (value: number | boolean | undefined): string => {
    if (value === undefined) return '-'
    if (typeof value === 'boolean') return value ? 'true' : 'false'
    return value.toFixed(2)
  }

  return (
    <Card className="min-w-[180px] border-2 border-orange-500">
      <div className="p-3 space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">{label}</span>
          <Badge variant="outline" className="text-xs">
            Command
          </Badge>
        </div>

        <div className="text-xs space-y-1 border-t pt-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Value:</span>
            <span className="font-mono font-semibold">
              {formatValue(inputValue)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Priority:</span>
            <span className="font-mono">{priority}</span>
          </div>
        </div>
      </div>

      <CustomHandle
        type="target"
        position={Position.Left}
        id={INPUT_HANDLE}
        className="w-3 h-3 bg-orange-500 border-2 border-background"
        connectionCount={1}
      />

      <Handle
        type="source"
        position={Position.Right}
        id={OUTPUT_HANDLE}
        className="w-3 h-3 bg-orange-500 border-2 border-background"
      />
    </Card>
  )
})

WriteSetpointNode.displayName = 'WriteSetpointNode'
