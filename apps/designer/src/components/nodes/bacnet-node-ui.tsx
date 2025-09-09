'use client'

import { memo, useState, useMemo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Plus, X, Info } from 'lucide-react'
import { PropertiesPanel } from './properties-panel'
import {
  getPropertyMetadata,
  BacnetProperties,
  StatusFlags,
} from '@/types/bacnet-properties'
import { BacnetInputOutput } from '@/types/infrastructure'

interface BacnetNodeUIProps extends NodeProps {
  data: BacnetInputOutput
}

export const BacnetNodeUI = memo(({ data }: BacnetNodeUIProps) => {
  const [showProperties, setShowProperties] = useState(false)

  // Local state for which properties to show in UI
  const [visibleProperties, setVisibleProperties] = useState<
    Set<keyof BacnetProperties>
  >(() => {
    // Start with presentValue and statusFlags if available
    const initial = new Set<keyof BacnetProperties>()
    if (data.discoveredProperties.presentValue !== undefined) {
      initial.add('presentValue')
    }
    if (data.discoveredProperties.statusFlags !== undefined) {
      initial.add('statusFlags')
    }
    return initial
  })

  // Get list of discovered properties that aren't visible
  const availableToAdd = useMemo(() => {
    const discovered = Object.keys(
      data.discoveredProperties
    ) as (keyof BacnetProperties)[]
    return discovered.filter((prop) => !visibleProperties.has(prop))
  }, [data.discoveredProperties, visibleProperties])

  // Add property to visible list
  const addProperty = (propertyName: keyof BacnetProperties) => {
    setVisibleProperties((prev) => new Set(prev).add(propertyName))
  }

  // Remove property from visible list
  const removeProperty = (propertyName: keyof BacnetProperties) => {
    setVisibleProperties((prev) => {
      const next = new Set(prev)
      next.delete(propertyName)
      return next
    })
  }

  return (
    <>
      <Card className="min-w-[200px] border-2">
        <div className="p-3">
          {/* Header with info button */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">{data.name}</span>
            <div className="flex items-center gap-1">
              <Badge variant="outline" className="text-xs">
                {data.objectType}
              </Badge>
              <Button
                size="icon"
                variant="ghost"
                className="h-6 w-6"
                onClick={(e) => {
                  e.stopPropagation() // Prevent node selection
                  setShowProperties(true)
                }}
                title="View all properties"
              >
                <Info className="h-3 w-3" />
              </Button>
            </div>
          </div>

          {/* Visible Properties */}
          <div className="space-y-2">
            {Array.from(visibleProperties).map((propertyName) => {
              const value = data.discoveredProperties[propertyName]
              const metadata = getPropertyMetadata(
                data.objectType,
                propertyName
              )

              if (value === undefined || !metadata) return null

              return (
                <div key={propertyName} className="relative group">
                  {/* Property row with handles */}
                  <div className="flex items-center gap-2">
                    {/* Input handle if writable */}
                    {metadata.writable && (
                      <Handle
                        type="target"
                        position={Position.Left}
                        id={`${propertyName}$input`}
                        className="!relative !top-auto !left-auto !transform-none w-2 h-2 bg-primary"
                        style={{ position: 'relative' }}
                      />
                    )}

                    {/* Property display */}
                    <div className="flex-1 text-xs">
                      <div className="text-muted-foreground">
                        {metadata.name}:
                      </div>
                      <div className="font-medium">
                        {formatPropertyValue(propertyName, value, data)}
                      </div>
                    </div>

                    {/* Output handle if readable */}
                    {metadata.readable && (
                      <Handle
                        type="source"
                        position={Position.Right}
                        id={`${propertyName}$output`}
                        className="!relative !top-auto !right-auto !transform-none w-2 h-2 bg-primary"
                        style={{ position: 'relative' }}
                      />
                    )}

                    {/* Remove button */}
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-4 w-4 opacity-0 group-hover:opacity-100"
                      onClick={() => removeProperty(propertyName)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Add Property Dropdown */}
          {availableToAdd.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  size="sm"
                  variant="ghost"
                  className="w-full mt-2 h-6 text-xs"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Property
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {availableToAdd.map((propertyName) => {
                  const metadata = getPropertyMetadata(
                    data.objectType,
                    propertyName
                  )
                  return (
                    <DropdownMenuItem
                      key={propertyName}
                      onClick={() => addProperty(propertyName)}
                    >
                      {metadata?.name || propertyName}
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </Card>

      <PropertiesPanel
        isOpen={showProperties}
        onClose={() => setShowProperties(false)}
        node={data}
      />
    </>
  )
})

BacnetNodeUI.displayName = 'BacnetNodeUI'

// Helper to format property values for display
function formatPropertyValue(
  propertyName: keyof BacnetProperties,
  value: BacnetProperties[keyof BacnetProperties],
  data: BacnetInputOutput
): string {
  if (value === null || value === undefined) return 'N/A'

  // Handle StatusFlags specially
  if (propertyName === 'statusFlags' && typeof value === 'object') {
    const flags = value as StatusFlags
    const active = []
    if (flags.inAlarm) active.push('Alarm')
    if (flags.fault) active.push('Fault')
    if (flags.overridden) active.push('Override')
    if (flags.outOfService) active.push('OOS')
    return active.join(', ') || 'Normal'
  }

  // Handle stateText array display (skip null at index 0)
  if (propertyName === 'stateText' && Array.isArray(value)) {
    return value
      .filter((text) => text !== null) // Filter out null
      .map((text, i) => `${i + 1}: ${text}`)
      .join(', ')
  }

  // Handle multistate presentValue with stateText lookup
  if (
    propertyName === 'presentValue' &&
    data.objectType.includes('multistate') &&
    typeof value === 'number'
  ) {
    const stateText = data.discoveredProperties.stateText as
      | string[]
      | undefined
    if (stateText && stateText[value]) {
      return `${stateText[value]} (${value})`
    }
    return `State ${value}`
  }

  // Handle units if present (for non-multistate objects)
  if (
    propertyName === 'presentValue' &&
    !data.objectType.includes('multistate')
  ) {
    const units = data.discoveredProperties.units
    if (units) {
      return `${value} ${units}`
    }
  }

  return String(value)
}
