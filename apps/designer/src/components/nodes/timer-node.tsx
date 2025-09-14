'use client'

import { memo, useState, useCallback, useEffect } from 'react'
import { NodeProps, Position, Handle } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CustomHandle } from './custom-handle'
import { TimerNodeData } from '@/types/node-data-types'
import { Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { useFlowStore } from '@/store/use-flow-store'

export const TimerNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as TimerNodeData
  const updateNode = useFlowStore((state) => state.updateNode)

  const [isEditingDuration, setIsEditingDuration] = useState(false)
  const [tempDuration, setTempDuration] = useState(
    typedData.metadata.duration.toString()
  )

  const [isRunning, setIsRunning] = useState(false)
  const [tickCount, setTickCount] = useState(0)

  useEffect(() => {
    typedData.stateDidChange = (stateData) => {
      setIsRunning(stateData.running)
      setTickCount(stateData.tickCount)
    }
    return () => {
      typedData.stateDidChange = undefined
    }
  }, [typedData])

  const handleDurationBlur = useCallback(() => {
    const newDuration = parseInt(tempDuration)
    if (!isNaN(newDuration) && newDuration >= 100) {
      updateNode({
        type: 'UPDATE_TIMER_DURATION',
        nodeId: id,
        duration: newDuration,
      })
    } else {
      setTempDuration(typedData.metadata.duration.toString())
    }
    setIsEditingDuration(false)
  }, [id, tempDuration, typedData.metadata.duration, updateNode])

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <Card
      className={cn(
        'min-w-[180px] border-2',
        isRunning ? 'border-green-500' : 'border-orange-500'
      )}
    >
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock
              className={cn(
                'h-4 w-4',
                isRunning ? 'text-green-500 animate-pulse' : 'text-orange-500'
              )}
            />
            <span className="text-sm font-medium">{typedData.label}</span>
          </div>
          <Badge variant="outline" className="text-xs">
            Timer
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Interval:</span>
          {isEditingDuration ? (
            <Input
              type="number"
              value={tempDuration}
              onChange={(e) => setTempDuration(e.target.value)}
              onBlur={handleDurationBlur}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleDurationBlur()
                }
              }}
              className="h-6 flex-1 text-xs"
              placeholder="ms"
              min="100"
              autoFocus
            />
          ) : (
            <div
              className="h-6 px-2 py-1 text-xs border rounded cursor-pointer hover:bg-accent flex-1 flex items-center justify-center"
              onClick={() => {
                setIsEditingDuration(true)
                setTempDuration(typedData.metadata.duration.toString())
              }}
            >
              {formatDuration(typedData.metadata.duration)}
            </div>
          )}
        </div>

        <div className="border-t pt-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Status:</span>
            <span
              className={cn(
                'font-medium',
                isRunning ? 'text-green-600' : 'text-gray-500'
              )}
            >
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-muted-foreground">Ticks:</span>
            <span className="font-mono font-bold">{tickCount}</span>
          </div>
        </div>
      </div>

      <CustomHandle
        type="target"
        position={Position.Left}
        id="trigger"
        className="w-3 h-3 bg-orange-500 border-2 border-background"
        connectionCount={1}
      />

      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className={cn(
          'w-3 h-3 border-2 border-background',
          isRunning ? 'bg-green-500' : 'bg-orange-500'
        )}
      />
    </Card>
  )
})

TimerNode.displayName = 'TimerNode'
