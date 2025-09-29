import 'server-only'

import { eq } from 'drizzle-orm'
import { getDatabase } from './client'
import {
  deploymentConfig,
  type DeploymentConfig,
  type InsertDeploymentConfig,
  type UpdateDeploymentConfig,
} from './schema'
import { randomUUID } from 'crypto'

export class DeploymentConfigRepository {
  private get db() {
    return getDatabase()
  }

  async getByProjectId(projectId: string): Promise<DeploymentConfig | null> {
    const config = await this.db
      .select()
      .from(deploymentConfig)
      .where(eq(deploymentConfig.project_id, projectId))
      .get()

    return config || null
  }

  async createOrUpdate(
    projectId: string,
    data:
      | UpdateDeploymentConfig
      | { organization_id: string; site_id: string; iot_device_id: string }
  ): Promise<DeploymentConfig> {
    const existing = await this.getByProjectId(projectId)
    const now = new Date().toISOString()

    if (existing) {
      const updatedConfig: Partial<DeploymentConfig> = {
        organization_id: data.organization_id ?? existing.organization_id,
        site_id: data.site_id ?? existing.site_id,
        iot_device_id: data.iot_device_id ?? existing.iot_device_id,
        updated_at: now,
      }

      await this.db
        .update(deploymentConfig)
        .set(updatedConfig)
        .where(eq(deploymentConfig.project_id, projectId))
        .run()

      const result = await this.db
        .select()
        .from(deploymentConfig)
        .where(eq(deploymentConfig.project_id, projectId))
        .get()

      return result!
    } else {
      if (!data.organization_id || !data.site_id || !data.iot_device_id) {
        throw new Error(
          'Required fields missing for new deployment config: organization_id, site_id, iot_device_id'
        )
      }

      const id = randomUUID()

      const newConfig: InsertDeploymentConfig = {
        id,
        project_id: projectId,
        organization_id: data.organization_id,
        site_id: data.site_id,
        iot_device_id: data.iot_device_id,
        created_at: now,
        updated_at: now,
      }

      await this.db.insert(deploymentConfig).values(newConfig).run()

      const result = await this.db
        .select()
        .from(deploymentConfig)
        .where(eq(deploymentConfig.id, id))
        .get()

      return result!
    }
  }

  async delete(projectId: string): Promise<void> {
    await this.db
      .delete(deploymentConfig)
      .where(eq(deploymentConfig.project_id, projectId))
      .run()
  }
}

export const deploymentConfigRepository = new DeploymentConfigRepository()
