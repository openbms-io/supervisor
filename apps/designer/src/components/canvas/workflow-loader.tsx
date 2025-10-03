'use client'

import { useEffect, useState, useCallback } from 'react'
import { Loader2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFlowStore } from '@/store/use-flow-store'
import { useDeploymentConfig } from '@/hooks/use-deployment-config'

interface WorkflowLoaderProps {
  projectId: string
}

export function WorkflowLoader({ projectId }: WorkflowLoaderProps) {
  const { data: deploymentConfig } = useDeploymentConfig(projectId)

  const loadProject = useFlowStore((s) => s.loadProject)
  const showError = useFlowStore((s) => s.showError)
  const startMqtt = useFlowStore((s) => s.startMqtt)
  const stopMqtt = useFlowStore((s) => s.stopMqtt)
  const clearAllNodes = useFlowStore((s) => s.clearAllNodes)
  const connectionStatus = useFlowStore((s) => s.connectionStatus)

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // MQTT lifecycle management - stop/start when deployment config changes
  useEffect(() => {
    if (!deploymentConfig) return

    clearAllNodes()
    startMqtt({
      organizationId: deploymentConfig.organization_id,
      siteId: deploymentConfig.site_id,
      iotDeviceId: deploymentConfig.iot_device_id,
    })

    return () => {
      clearAllNodes()
      stopMqtt()
    }
  }, [
    deploymentConfig?.organization_id,
    deploymentConfig?.site_id,
    deploymentConfig?.iot_device_id,
    startMqtt,
    stopMqtt,
    clearAllNodes,
    deploymentConfig,
  ])

  const doLoad = useCallback(async () => {
    if (!deploymentConfig) {
      setIsLoading(false)
      return
    }

    // Wait for MQTT connection before loading workflow
    if (connectionStatus !== 'connected') {
      setIsLoading(true)
      return // Don't load yet, wait for connection
    }

    setIsLoading(true)
    setError(null)
    try {
      await loadProject({ projectId })
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to load workflow'
      setError(msg)
      showError('Load Failed', msg)
    } finally {
      setIsLoading(false)
    }
  }, [loadProject, projectId, showError, deploymentConfig, connectionStatus])

  // Load workflow after MQTT is connected
  useEffect(() => {
    void doLoad()
  }, [doLoad])

  return (
    <>
      {isLoading && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-background/60 backdrop-blur-[1px]">
          <div className="flex items-center gap-3 rounded-md border border-border bg-card px-4 py-3 shadow-sm">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading workflow…</span>
          </div>
        </div>
      )}

      {!isLoading && error && (
        <div className="fixed top-16 right-6 z-40 max-w-sm rounded-md border border-border bg-card p-4 shadow-md">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
            <div className="flex-1">
              <div className="font-medium text-sm">Failed to load workflow</div>
              <div className="text-xs text-muted-foreground mt-1 break-words">
                {error}
              </div>
              <div className="mt-3 flex gap-2">
                <Button size="sm" onClick={() => void doLoad()}>
                  Retry
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
