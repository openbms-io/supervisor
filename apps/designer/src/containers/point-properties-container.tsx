'use client'

// Internal absolute imports
import { useInfrastructureStore } from '@/store/use-infrastructure-store'
import { BacnetConfig } from '@/types/infrastructure'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

export function PointPropertiesContainer() {
  const { selectedPointId, supervisors } = useInfrastructureStore()

  // Find the selected point
  let selectedPoint: BacnetConfig | null = null
  let controllerName = ''
  let supervisorName = ''

  if (selectedPointId) {
    for (const supervisor of supervisors.values()) {
      for (const controller of supervisor.controllers) {
        const point = controller.discoveredPoints.find(
          (p) => p.pointId === selectedPointId
        )
        if (point) {
          selectedPoint = point
          controllerName = controller.name
          supervisorName = supervisor.name
          break
        }
      }
      if (selectedPoint) break
    }
  }

  if (!selectedPoint) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p className="text-sm">Select a point to view its properties</p>
      </div>
    )
  }

  return (
    <Card className="m-4">
      <CardHeader>
        <CardTitle className="text-lg">{selectedPoint.name}</CardTitle>
        <CardDescription>
          {supervisorName} / {controllerName}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Basic Information</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Object Type:</span>
                <Badge variant="outline">{selectedPoint.objectType}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Object ID:</span>
                <span className="font-mono">{selectedPoint.objectId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Point ID:</span>
                <span className="font-mono text-xs">
                  {selectedPoint.pointId}
                </span>
              </div>
            </div>
          </div>

          <Separator />

          <div>
            <h4 className="text-sm font-medium mb-2">Current Value</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Present Value:</span>
                <span className="font-semibold">
                  {formatValue({
                    value:
                      selectedPoint.discoveredProperties.presentValue ?? 'N/A',
                    units: selectedPoint.discoveredProperties.units,
                  })}
                </span>
              </div>
              {selectedPoint.discoveredProperties.units && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Units:</span>
                  <span>{selectedPoint.discoveredProperties.units}</span>
                </div>
              )}
            </div>
          </div>

          {selectedPoint.discoveredProperties.description && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-medium mb-2">Description</h4>
                <p className="text-sm text-muted-foreground">
                  {selectedPoint.discoveredProperties.description}
                </p>
              </div>
            </>
          )}

          {(selectedPoint.discoveredProperties.minPresValue !== undefined ||
            selectedPoint.discoveredProperties.maxPresValue !== undefined) && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-medium mb-2">Limits</h4>
                <div className="space-y-2 text-sm">
                  {selectedPoint.discoveredProperties.minPresValue !==
                    undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Min Value:</span>
                      <span>
                        {selectedPoint.discoveredProperties.minPresValue}
                      </span>
                    </div>
                  )}
                  {selectedPoint.discoveredProperties.maxPresValue !==
                    undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Max Value:</span>
                      <span>
                        {selectedPoint.discoveredProperties.maxPresValue}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          <Separator />

          <div>
            <h4 className="text-sm font-medium mb-2">Metadata</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Supervisor ID:</span>
                <span className="font-mono text-xs">
                  {selectedPoint.supervisorId}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Controller ID:</span>
                <span className="font-mono text-xs">
                  {selectedPoint.controllerId}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function formatValue({
  value,
  units,
}: {
  value: string | number | boolean
  units?: string
}): string {
  if (typeof value === 'boolean') {
    return value ? 'ON' : 'OFF'
  }

  if (typeof value === 'number') {
    const formatted = value.toFixed(1)
    return units ? `${formatted} ${units}` : formatted
  }

  return String(value)
}
