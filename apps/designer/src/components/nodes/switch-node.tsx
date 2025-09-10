'use client'

import { memo, useState, useCallback } from 'react'
import { NodeProps, Position } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CustomHandle } from './custom-handle'
import { SwitchNodeData } from '@/types/node-data-types'
import { SwitchOutputHandle } from '@/types/infrastructure'
import { GitBranch, CheckCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useFlowStore } from '@/store/use-flow-store'

export const SwitchNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as SwitchNodeData
  const updateNode = useFlowStore((state) => state.updateNode)

  const [isEditingThreshold, setIsEditingThreshold] = useState(false)
  const [tempThreshold, setTempThreshold] = useState(
    typedData.threshold.toString()
  )

  const handleConditionChange = useCallback(
    (newCondition: string) => {
      updateNode({
        type: 'UPDATE_SWITCH_CONFIG',
        nodeId: id,
        condition: newCondition as 'gt' | 'lt' | 'eq' | 'gte' | 'lte',
        threshold: typedData.threshold,
      })
    },
    [id, typedData.threshold, updateNode]
  )

  const handleThresholdBlur = useCallback(() => {
    const newThreshold = parseFloat(tempThreshold)
    if (!isNaN(newThreshold)) {
      updateNode({
        type: 'UPDATE_SWITCH_CONFIG',
        nodeId: id,
        condition: typedData.condition,
        threshold: newThreshold,
      })
    } else {
      setTempThreshold(typedData.threshold.toString())
    }
    setIsEditingThreshold(false)
  }, [id, tempThreshold, typedData.condition, typedData.threshold, updateNode])

  // Subscribe to store changes for reactive updates
  const activeOutput = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    const nodeData = node?.data
    if (
      nodeData &&
      'getActiveOutputHandles' in nodeData &&
      typeof nodeData.getActiveOutputHandles === 'function'
    ) {
      const handles = nodeData.getActiveOutputHandles()
      return handles[0] as SwitchOutputHandle
    }
    return undefined
  })

  const formatValue = (value: unknown): string => {
    if (value === undefined || value === null) return 'N/A'
    if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE'
    if (typeof value === 'number') return value.toFixed(2)
    return String(value)
  }

  return (
    <Card className="min-w-[220px] border-2 border-dashed border-orange-500">
      <div className="p-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-orange-500" />
            <span className="text-sm font-medium">{typedData.label}</span>
          </div>
          <Badge variant="outline" className="text-xs">
            Switch
          </Badge>
        </div>

        {/* Input and Configuration */}
        <div className="mb-3 pb-3 border-b">
          <div className="flex items-center gap-2 mb-2">
            <CustomHandle
              type="target"
              position={Position.Left}
              id="input"
              className="!relative !top-auto !left-auto !transform-none w-2 h-2 bg-blue-500"
              style={{ position: 'relative' }}
            />
            <div className="text-xs flex-1">
              <div className="font-mono font-medium">
                Input: {formatValue(typedData.computedValue)}
              </div>
            </div>
          </div>

          {/* Condition and Threshold Configuration */}
          <div className="flex items-center gap-2 mt-2">
            <Select
              value={typedData.condition}
              onValueChange={handleConditionChange}
            >
              <SelectTrigger className="h-7 text-xs flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gt">Greater than (&gt;)</SelectItem>
                <SelectItem value="gte">Greater or equal (≥)</SelectItem>
                <SelectItem value="lt">Less than (&lt;)</SelectItem>
                <SelectItem value="lte">Less or equal (≤)</SelectItem>
                <SelectItem value="eq">Equals (=)</SelectItem>
              </SelectContent>
            </Select>

            {isEditingThreshold ? (
              <Input
                type="number"
                value={tempThreshold}
                onChange={(e) => setTempThreshold(e.target.value)}
                onBlur={handleThresholdBlur}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleThresholdBlur()
                  }
                }}
                className="h-7 w-20 text-xs"
                autoFocus
              />
            ) : (
              <div
                className="h-7 px-2 py-1 text-xs border rounded cursor-pointer hover:bg-accent flex items-center w-20 justify-center"
                onClick={() => {
                  setIsEditingThreshold(true)
                  setTempThreshold(typedData.threshold.toString())
                }}
              >
                {typedData.threshold}
              </div>
            )}
          </div>
        </div>

        {/* Outputs */}
        <div className="space-y-2">
          {/* Active output */}
          <div
            className={cn(
              'flex items-center justify-between px-2 py-1 rounded',
              activeOutput === 'active' && 'bg-green-100 dark:bg-green-900/20'
            )}
          >
            <span className="text-xs font-medium">{typedData.activeLabel}</span>
            <div className="flex items-center gap-1">
              {activeOutput === 'active' && (
                <CheckCircle className="h-3 w-3 text-green-600" />
              )}
              <CustomHandle
                type="source"
                position={Position.Right}
                id="active"
                className={cn(
                  '!relative !top-auto !right-auto !transform-none w-2 h-2',
                  activeOutput === 'active' ? 'bg-green-500' : 'bg-gray-400'
                )}
                style={{ position: 'relative' }}
              />
            </div>
          </div>

          {/* Inactive output */}
          <div
            className={cn(
              'flex items-center justify-between px-2 py-1 rounded',
              activeOutput === 'inactive' && 'bg-gray-100 dark:bg-gray-800/20'
            )}
          >
            <span className="text-xs font-medium">
              {typedData.inactiveLabel}
            </span>
            <div className="flex items-center gap-1">
              {activeOutput === 'inactive' && (
                <XCircle className="h-3 w-3 text-gray-600" />
              )}
              <CustomHandle
                type="source"
                position={Position.Right}
                id="inactive"
                className={cn(
                  '!relative !top-auto !right-auto !transform-none w-2 h-2',
                  activeOutput === 'inactive' ? 'bg-gray-500' : 'bg-gray-400'
                )}
                style={{ position: 'relative' }}
              />
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
})

SwitchNode.displayName = 'SwitchNode'
