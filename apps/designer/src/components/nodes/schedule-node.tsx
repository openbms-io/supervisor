'use client'

import { memo, useState, useCallback, useEffect } from 'react'
import { NodeProps, Position, Handle } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CustomHandle } from './custom-handle'
import { ScheduleNodeData } from '@/types/node-data-types'
import { Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { useFlowStore } from '@/store/use-flow-store'
import { DayOfWeek, ScheduleState } from '@/lib/data-nodes/schedule-node'

// Clean Day Selector Component
const DaySelector = ({
  selectedDays,
  onChange,
}: {
  selectedDays: DayOfWeek[]
  onChange: (days: DayOfWeek[]) => void
}) => {
  const allDays: DayOfWeek[] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const isAllDays = selectedDays.length === 7

  const toggleDay = (day: DayOfWeek) => {
    if (selectedDays.includes(day)) {
      const newDays = selectedDays.filter((d) => d !== day)
      if (newDays.length > 0) onChange(newDays)
    } else {
      onChange([...selectedDays, day])
    }
  }

  const toggleAll = () => {
    onChange(isAllDays ? ['Mon'] : allDays)
  }

  return (
    <div className="space-y-1">
      <button
        onClick={toggleAll}
        className={cn(
          'w-full h-6 text-xs rounded border transition-colors',
          isAllDays
            ? 'bg-blue-500 text-white border-blue-500'
            : 'hover:bg-accent border-input'
        )}
      >
        {isAllDays ? 'Every day' : 'Select days'}
      </button>

      {!isAllDays && (
        <div className="flex gap-1">
          {allDays.map((day) => (
            <button
              key={day}
              onClick={() => toggleDay(day)}
              className={cn(
                'flex-1 h-6 text-xs rounded border transition-colors',
                selectedDays.includes(day)
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'hover:bg-accent border-input'
              )}
            >
              {day}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export const ScheduleNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as ScheduleNodeData
  const updateNode = useFlowStore((state) => state.updateNode)

  // Single state from node
  const [scheduleState, setScheduleState] = useState<ScheduleState>({
    startTime: typedData.metadata.startTime,
    endTime: typedData.metadata.endTime,
    days: typedData.metadata.days,
    isActive: false,
    isEnabled: false,
  })

  // Temp values for editing
  const [tempStartTime, setTempStartTime] = useState(scheduleState.startTime)
  const [tempEndTime, setTempEndTime] = useState(scheduleState.endTime)

  useEffect(() => {
    // Receive full state object from node
    typedData.stateDidChange = (state: ScheduleState) => {
      setScheduleState(state)
      setTempStartTime(state.startTime)
      setTempEndTime(state.endTime)
    }
    return () => {
      typedData.stateDidChange = undefined
    }
  }, [typedData])

  const handleTimeChange = useCallback(() => {
    if (
      /^\d{2}:\d{2}$/.test(tempStartTime) &&
      /^\d{2}:\d{2}$/.test(tempEndTime)
    ) {
      updateNode({
        type: 'UPDATE_SCHEDULE_CONFIG',
        nodeId: id,
        startTime: tempStartTime,
        endTime: tempEndTime,
        days: scheduleState.days,
      })
    }
  }, [id, tempStartTime, tempEndTime, scheduleState.days, updateNode])

  const handleDaysChange = useCallback(
    (days: DayOfWeek[]) => {
      updateNode({
        type: 'UPDATE_SCHEDULE_CONFIG',
        nodeId: id,
        startTime: scheduleState.startTime,
        endTime: scheduleState.endTime,
        days,
      })
    },
    [id, scheduleState.startTime, scheduleState.endTime, updateNode]
  )

  return (
    <Card
      className={cn(
        'min-w-[220px] border-2',
        scheduleState.isActive ? 'border-green-500' : 'border-gray-400'
      )}
    >
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar
              className={cn(
                'h-4 w-4',
                scheduleState.isActive ? 'text-green-500' : 'text-gray-500'
              )}
            />
            <span className="text-sm font-medium">{typedData.label}</span>
          </div>
          <Badge variant="outline" className="text-xs">
            Schedule
          </Badge>
        </div>

        {/* Time Range */}
        <div className="flex items-center gap-1 text-xs">
          <Input
            type="text"
            value={tempStartTime}
            onChange={(e) => setTempStartTime(e.target.value)}
            onBlur={handleTimeChange}
            className="h-6 w-16 text-xs text-center font-mono"
            placeholder="HH:MM"
          />
          <span className="text-muted-foreground">-</span>
          <Input
            type="text"
            value={tempEndTime}
            onChange={(e) => setTempEndTime(e.target.value)}
            onBlur={handleTimeChange}
            className="h-6 w-16 text-xs text-center font-mono"
            placeholder="HH:MM"
          />
        </div>

        {/* Day Selector */}
        <DaySelector
          selectedDays={scheduleState.days}
          onChange={handleDaysChange}
        />

        {/* Status */}
        <div className="border-t pt-2 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            {scheduleState.isEnabled
              ? scheduleState.isActive
                ? 'Active'
                : 'Waiting'
              : 'Disabled'}
          </span>
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              scheduleState.isEnabled
                ? scheduleState.isActive
                  ? 'bg-green-500'
                  : 'bg-yellow-500'
                : 'bg-gray-400'
            )}
          />
        </div>
      </div>

      <CustomHandle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 bg-gray-500 border-2 border-background"
        connectionCount={1}
      />

      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className={cn(
          'w-3 h-3 border-2 border-background',
          scheduleState.isActive ? 'bg-green-500' : 'bg-gray-500'
        )}
      />
    </Card>
  )
})

ScheduleNode.displayName = 'ScheduleNode'
