import {
  DeploymentConfig,
  UpdateDeploymentConfig,
  DeploymentConfigResponseSchema,
} from '@/app/api/deployment-config/schemas'
import { withRetry, handleResponse } from './utils'

export const deploymentConfigApi = {
  async get(): Promise<DeploymentConfig> {
    const result = await withRetry(async () => {
      const response = await fetch('/api/deployment-config')
      return handleResponse(response)
    })

    const parsed = DeploymentConfigResponseSchema.parse(result)

    if (!parsed.success || !parsed.config) {
      throw new Error(parsed.error || 'Failed to get deployment config')
    }

    return parsed.config
  },

  async update(data: UpdateDeploymentConfig): Promise<DeploymentConfig> {
    const result = await withRetry(async () => {
      const response = await fetch('/api/deployment-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      return handleResponse(response)
    })

    const parsed = DeploymentConfigResponseSchema.parse(result)

    if (!parsed.success || !parsed.config) {
      throw new Error(parsed.error || 'Failed to update deployment config')
    }

    return parsed.config
  },
}
