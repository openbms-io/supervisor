'use client'

import { memo, useCallback, useState, useEffect } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useFlowStore } from '@/store/use-flow-store'
import type { ValueType } from '@/lib/data-nodes/constant-node'
import { ConstantNodeData } from '@/types/node-data-types'

export const ConstantNodeUI = memo(({ data, id }: NodeProps) => {
  const typedData = data as ConstantNodeData
  const { label, metadata } = typedData
  const updateNode = useFlowStore((state) => state.updateNode)

  // Get value from metadata
  const storeValue = metadata.value

  const valueType = metadata.valueType

  // label is already available from data destructuring

  // Local state for immediate UI feedback
  const [localValue, setLocalValue] = useState<string>(String(storeValue))

  // Update local value when store value changes (e.g., from undo/redo or external updates)
  useEffect(() => {
    setLocalValue(String(storeValue))
  }, [storeValue])

  const handleTypeChange = useCallback(
    (newType: ValueType) => {
      updateNode({
        type: 'UPDATE_CONSTANT_TYPE',
        nodeId: id,
        valueType: newType,
      })
    },
    [id, updateNode]
  )

  // Update value immediately without executing graph
  const handleValueChange = useCallback(
    (newValue: number | boolean | string) => {
      updateNode({
        type: 'UPDATE_CONSTANT_VALUE',
        nodeId: id,
        value: newValue,
      })
    },
    [id, updateNode]
  )

  const renderValueInput = () => {
    switch (valueType) {
      case 'number':
        return (
          <Input
            type="number"
            value={localValue}
            onChange={(e) => {
              const value = e.target.value
              setLocalValue(value)
              const numValue = parseFloat(value)
              if (!isNaN(numValue)) {
                handleValueChange(numValue)
              }
            }}
            className="h-8 text-center"
          />
        )
      case 'boolean':
        return (
          <div className="flex items-center justify-center gap-2 py-1">
            <span className="text-xs text-muted-foreground">False</span>
            <Switch
              checked={storeValue as boolean}
              onCheckedChange={(checked) => {
                handleValueChange(checked)
              }}
            />
            <span className="text-xs text-muted-foreground">True</span>
          </div>
        )
      case 'string':
        return (
          <Input
            type="text"
            value={localValue}
            onChange={(e) => {
              const value = e.target.value
              setLocalValue(value)
              handleValueChange(value)
            }}
            className="h-8"
            placeholder="Enter text..."
          />
        )
    }
  }

  return (
    <Card className="min-w-[180px] border-2 border-gray-400">
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">{label || 'Constant'}</span>
          <Badge variant="secondary" className="text-xs">
            {valueType}
          </Badge>
        </div>

        {/* Type Selector */}
        <Select value={valueType} onValueChange={handleTypeChange}>
          <SelectTrigger className="h-7 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="number">Number</SelectItem>
            <SelectItem value="boolean">Boolean</SelectItem>
            <SelectItem value="string">String</SelectItem>
          </SelectContent>
        </Select>

        {/* Value Input */}
        {renderValueInput()}
      </div>

      {/* Trigger Input Handle - purely for visual connection */}
      <Handle
        type="target"
        position={Position.Left}
        id="trigger"
        className="w-3 h-3 bg-gray-500 border-2 border-background"
      />

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="w-3 h-3 bg-gray-500 border-2 border-background"
      />
    </Card>
  )
})

ConstantNodeUI.displayName = 'ConstantNodeUI'
