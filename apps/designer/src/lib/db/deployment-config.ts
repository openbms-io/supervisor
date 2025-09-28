import 'server-only'

import { eq } from 'drizzle-orm'
import { getDatabase } from './client'
import {
  deploymentConfig,
  type DeploymentConfig,
  type InsertDeploymentConfig,
} from './schema'
import { randomUUID } from 'crypto'

export class DeploymentConfigRepository {
  private get db() {
    return getDatabase()
  }

  async getOrCreate(): Promise<DeploymentConfig> {
    const existing = await this.db.select().from(deploymentConfig).get()

    if (existing) {
      return existing
    }

    const id = randomUUID()
    const now = new Date().toISOString()

    const defaultConfig: InsertDeploymentConfig = {
      id,
      organization_id: 'org_default',
      site_id: 'default_site',
      device_id: 'default_device',
      created_at: now,
      updated_at: now,
    }

    await this.db.insert(deploymentConfig).values(defaultConfig).run()

    const created = await this.db
      .select()
      .from(deploymentConfig)
      .where(eq(deploymentConfig.id, id))
      .get()

    return created!
  }

  async update(
    data: Partial<
      Pick<DeploymentConfig, 'organization_id' | 'site_id' | 'device_id'>
    >
  ): Promise<DeploymentConfig> {
    const existing = await this.getOrCreate()

    const newId = randomUUID()
    const now = new Date().toISOString()

    const updatedConfig: InsertDeploymentConfig = {
      id: newId,
      organization_id: data.organization_id ?? existing.organization_id,
      site_id: data.site_id ?? existing.site_id,
      device_id: data.device_id ?? existing.device_id,
      created_at: now,
      updated_at: now,
    }

    await this.db.delete(deploymentConfig).run()

    await this.db.insert(deploymentConfig).values(updatedConfig).run()

    const result = await this.db
      .select()
      .from(deploymentConfig)
      .where(eq(deploymentConfig.id, newId))
      .get()

    return result!
  }
}

export const deploymentConfigRepository = new DeploymentConfigRepository()
