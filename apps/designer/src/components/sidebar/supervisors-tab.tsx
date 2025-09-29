'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, AlertCircle, Edit, Save, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  useDeploymentConfig,
  useUpdateDeploymentConfig,
} from '@/hooks/use-deployment-config'

interface SupervisorsTabProps {
  projectId: string
}

export function SupervisorsTab({ projectId }: SupervisorsTabProps) {
  const { data: deploymentConfig, isLoading } = useDeploymentConfig(projectId)
  const updateConfigMutation = useUpdateDeploymentConfig(projectId)

  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    organization_id: '',
    site_id: '',
    iot_device_id: '',
  })

  const hasConfig = !!deploymentConfig

  useEffect(() => {
    if (deploymentConfig) {
      setFormData({
        organization_id: deploymentConfig.organization_id,
        site_id: deploymentConfig.site_id,
        iot_device_id: deploymentConfig.iot_device_id,
      })
    }
  }, [deploymentConfig])

  const handleSave = async () => {
    if (
      !formData.organization_id.trim() ||
      !formData.site_id.trim() ||
      !formData.iot_device_id.trim()
    ) {
      return
    }

    try {
      await updateConfigMutation.mutateAsync(formData)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save deployment config:', error)
    }
  }

  const handleCancel = () => {
    if (deploymentConfig) {
      setFormData({
        organization_id: deploymentConfig.organization_id,
        site_id: deploymentConfig.site_id,
        iot_device_id: deploymentConfig.iot_device_id,
      })
    } else {
      setFormData({
        organization_id: '',
        site_id: '',
        iot_device_id: '',
      })
    }
    setIsEditing(false)
  }

  const getStatus = () => {
    if (isLoading) return 'loading'
    if (!hasConfig) return 'not-configured'
    return 'configured'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'configured':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'not-configured':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'configured':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'not-configured':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const status = getStatus()

  if (isLoading) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-3 border-b">
          <h3 className="text-sm font-medium">Supervisors</h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">Supervisors</h3>
          {hasConfig && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="p-1 rounded-md hover:bg-accent transition-colors"
            >
              <Edit className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Configuration Form/Display */}
      <div className="flex-1 p-3">
        {!hasConfig && !isEditing ? (
          <div className="space-y-4">
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h4 className="text-sm font-medium mb-2">
                No Supervisor Configured
              </h4>
              <p className="text-xs text-muted-foreground mb-4">
                Configure deployment settings to set up your supervisor.
              </p>
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
              >
                Configure Supervisor
              </button>
            </div>
          </div>
        ) : isEditing ? (
          <div className="space-y-4">
            <h4 className="text-sm font-medium">
              {hasConfig ? 'Edit' : 'Configure'} Deployment Settings
            </h4>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Organization ID
                </label>
                <input
                  type="text"
                  placeholder="org_example"
                  value={formData.organization_id}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      organization_id: e.target.value,
                    }))
                  }
                  className="w-full mt-1 px-2 py-1 text-xs border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Must start with &quot;org_&quot;
                </p>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Site ID
                </label>
                <input
                  type="text"
                  placeholder="uuid"
                  value={formData.site_id}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      site_id: e.target.value,
                    }))
                  }
                  className="w-full mt-1 px-2 py-1 text-xs border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  IoT Device ID
                </label>
                <input
                  type="text"
                  placeholder="uuid"
                  value={formData.iot_device_id}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      iot_device_id: e.target.value,
                    }))
                  }
                  className="w-full mt-1 px-2 py-1 text-xs border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Unique identifier for MQTT topics
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={
                  !formData.organization_id.trim() ||
                  !formData.site_id.trim() ||
                  !formData.iot_device_id.trim() ||
                  !formData.organization_id.startsWith('org_') ||
                  updateConfigMutation.isPending
                }
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded disabled:bg-muted disabled:text-muted-foreground transition-colors"
              >
                <Save className="w-3 h-3" />
                {updateConfigMutation.isPending ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={handleCancel}
                className="flex items-center gap-1 px-3 py-1.5 text-xs border rounded hover:bg-accent transition-colors"
              >
                <X className="w-3 h-3" />
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3 border rounded-lg bg-card">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getStatusIcon(status)}
                  <div>
                    <div className="text-sm font-medium">
                      Supervisor Configured
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Ready for MQTT communication
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-2 mt-3">
                <div>
                  <span className="text-xs font-medium text-muted-foreground">
                    Organization:
                  </span>
                  <span className="text-xs ml-2">
                    {deploymentConfig!.organization_id}
                  </span>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">
                    Site:
                  </span>
                  <span className="text-xs ml-2">
                    {deploymentConfig!.site_id}
                  </span>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">
                    Device ID:
                  </span>
                  <span className="text-xs ml-2">
                    {deploymentConfig!.iot_device_id}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between mt-3">
                <span
                  className={cn(
                    'px-2 py-1 text-xs rounded-full border',
                    getStatusColor(status)
                  )}
                >
                  {status === 'configured' ? 'Configured' : 'Not Configured'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t bg-muted/30">
        <div className="text-xs text-muted-foreground">
          Supervisors manage IoT controllers and execute visual programming
          flows via MQTT.
        </div>
      </div>
    </div>
  )
}
