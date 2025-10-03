import {
  DeploymentConfig,
  UpdateDeploymentConfig,
  DeploymentConfigResponseSchema,
} from '@/app/api/projects/[id]/deployment-config/schemas'
import { withRetry, handleResponse } from './utils'

export const deploymentConfigApi = {
  async get(projectId: string): Promise<DeploymentConfig | null> {
    const result = await withRetry(async () => {
      const response = await fetch(
        `/api/projects/${projectId}/deployment-config`
      )
      return handleResponse(response)
    })

    const parsed = DeploymentConfigResponseSchema.parse(result)

    if (!parsed.success) {
      throw new Error(parsed.error || 'Failed to get deployment config')
    }

    return parsed.config || null
  },

  async update(
    projectId: string,
    data: UpdateDeploymentConfig
  ): Promise<DeploymentConfig> {
    const result = await withRetry(async () => {
      const response = await fetch(
        `/api/projects/${projectId}/deployment-config`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        }
      )
      return handleResponse(response)
    })

    const parsed = DeploymentConfigResponseSchema.parse(result)

    if (!parsed.success || !parsed.config) {
      throw new Error(
        parsed.success === false
          ? parsed.error
          : 'Failed to update deployment config'
      )
    }

    return parsed.config
  },

  async delete(projectId: string): Promise<void> {
    const result = await withRetry(async () => {
      const response = await fetch(
        `/api/projects/${projectId}/deployment-config`,
        {
          method: 'DELETE',
        }
      )
      return handleResponse(response)
    })

    const parsed = DeploymentConfigResponseSchema.parse(result)

    if (!parsed.success) {
      throw new Error(parsed.error || 'Failed to delete deployment config')
    }
  },
}
