'use client'

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { BacnetInputOutput } from '@/types/infrastructure'
import {
  getPropertyMetadata,
  BacnetProperties,
  StatusFlags,
} from '@/types/bacnet-properties'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface PropertiesPanelProps {
  isOpen: boolean
  onClose: () => void
  node: BacnetInputOutput | null
}

export function PropertiesPanel({
  isOpen,
  onClose,
  node,
}: PropertiesPanelProps) {
  if (!node) return null

  const properties = Object.entries(node.discoveredProperties)
    .filter(([, value]) => value !== undefined && value !== null)
    .sort(([a], [b]) => a.localeCompare(b))

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>{node.name} Properties</SheetTitle>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline" className="w-fit">
              {node.objectType}
            </Badge>
            <Badge variant="secondary" className="w-fit">
              {properties.length} properties
            </Badge>
          </div>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-140px)] mt-6">
          <div className="space-y-4 pr-4">
            {properties.map(([key, value]) => {
              const metadata = getPropertyMetadata(
                node.objectType,
                key as keyof BacnetProperties
              )

              return (
                <div key={key} className="border-b pb-3 last:border-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">
                      {metadata?.name || key}
                    </span>
                    <div className="flex gap-1">
                      {metadata?.readable && (
                        <Badge variant="secondary" className="text-xs h-5 px-1">
                          R
                        </Badge>
                      )}
                      {metadata?.writable && (
                        <Badge variant="secondary" className="text-xs h-5 px-1">
                          W
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground font-mono">
                    {formatPropertyValue(
                      key as keyof BacnetProperties,
                      value,
                      node
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}

// Reuse formatting logic from BacnetNodeUI
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
      .filter((text) => text !== null)
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

  // Handle arrays
  if (Array.isArray(value)) {
    return `[${value.join(', ')}]`
  }

  // Handle objects
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }

  return String(value)
}
