'use client'

import { memo, useCallback } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch as Toggle } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { useFlowStore } from '@/store/use-flow-store'
import { MemoryNodeData } from '@/types/node-data-types'

export const MemoryNodeUI = memo(({ data, id }: NodeProps) => {
  const typed = data as MemoryNodeData
  const { label, metadata } = typed
  const updateNode = useFlowStore((state) => state.updateNode)

  const current = typed.getValue ? typed.getValue() : undefined

  const onInitChange = useCallback(
    (value: number | boolean) => {
      updateNode({ type: 'UPDATE_MEMORY_INIT', nodeId: id, initValue: value })
    },
    [id, updateNode]
  )

  const onTypeChange = useCallback(
    (v: 'number' | 'boolean') => {
      updateNode({ type: 'UPDATE_MEMORY_TYPE', nodeId: id, valueType: v })
    },
    [id, updateNode]
  )

  const onReset = useCallback(() => {
    updateNode({ type: 'RESET_MEMORY_NOW', nodeId: id })
  }, [id, updateNode])

  return (
    <Card className="min-w-[200px] border-2 border-indigo-400">
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            {label || 'Memory/Register'}
          </span>
          <Badge variant="secondary" className="text-xs">
            {metadata.valueType}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex flex-col gap-1">
            <span className="text-muted-foreground">Init</span>
            {metadata.valueType === 'number' ? (
              <Input
                type="number"
                className="h-7"
                value={Number(metadata.initValue)}
                onChange={(e) => onInitChange(parseFloat(e.target.value))}
              />
            ) : (
              <div className="flex items-center justify-between py-1">
                <span>False</span>
                <Toggle
                  checked={Boolean(metadata.initValue)}
                  onCheckedChange={(c) => onInitChange(c)}
                />
                <span>True</span>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-muted-foreground">Current</span>
            <div className="h-7 rounded-md border flex items-center justify-center bg-muted">
              <span className="text-sm">
                {current === undefined ? '—' : String(current)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">Type</span>
          <div className="flex gap-2">
            <Button
              variant={metadata.valueType === 'number' ? 'default' : 'outline'}
              size="xs"
              onClick={() => onTypeChange('number')}
            >
              Number
            </Button>
            <Button
              variant={metadata.valueType === 'boolean' ? 'default' : 'outline'}
              size="xs"
              onClick={() => onTypeChange('boolean')}
            >
              Boolean
            </Button>
          </div>
          <div className="flex-1" />
          <Button variant="outline" size="xs" onClick={onReset}>
            Reset
          </Button>
        </div>
      </div>

      {/* Input handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="value"
        className="w-3 h-3 bg-indigo-500 border-2 border-background"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="write"
        style={{ top: '50%' }}
        className="w-3 h-3 bg-green-500 border-2 border-background"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="reset"
        style={{ top: '80%' }}
        className="w-3 h-3 bg-red-500 border-2 border-background"
      />

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="w-3 h-3 bg-indigo-500 border-2 border-background"
      />
    </Card>
  )
})

MemoryNodeUI.displayName = 'MemoryNodeUI'
