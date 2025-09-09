'use client'

import { memo, useCallback } from 'react'
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
import type {
  ValueType,
  ConstantNodeMetadata,
} from '@/lib/data-nodes/constant-node'

interface ConstantData {
  label: string
  value: number | boolean | string
  valueType: ValueType
}

export const ConstantNodeUI = memo(({ id }: NodeProps<ConstantData>) => {
  const updateNode = useFlowStore((state) => state.updateNode)

  // Subscribe to specific values separately to avoid infinite loops
  const value = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    const metadata = (node?.data as { metadata?: ConstantNodeMetadata })
      ?.metadata
    return metadata?.value ?? 0
  })

  const valueType = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    const metadata = (node?.data as { metadata?: ConstantNodeMetadata })
      ?.metadata
    return metadata?.valueType ?? ('number' as ValueType)
  })

  const label = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    return (node?.data as { label?: string })?.label ?? 'Constant'
  })

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
            value={value as number}
            onChange={(e) => handleValueChange(parseFloat(e.target.value) || 0)}
            className="h-8 text-center"
          />
        )
      case 'boolean':
        return (
          <div className="flex items-center justify-center gap-2 py-1">
            <span className="text-xs text-muted-foreground">False</span>
            <Switch
              checked={value as boolean}
              onCheckedChange={handleValueChange}
            />
            <span className="text-xs text-muted-foreground">True</span>
          </div>
        )
      case 'string':
        return (
          <Input
            type="text"
            value={value as string}
            onChange={(e) => handleValueChange(e.target.value)}
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

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-gray-500 border-2 border-background"
      />
    </Card>
  )
})

ConstantNodeUI.displayName = 'ConstantNodeUI'
