import { sql } from 'drizzle-orm'
import { text, sqliteTable, index, unique } from 'drizzle-orm/sqlite-core'
import { projects } from './projects'

export const deploymentConfig = sqliteTable(
  'deployment_config',
  {
    id: text('id').primaryKey(),
    project_id: text('project_id')
      .notNull()
      .references(() => projects.id, { onDelete: 'cascade' }),
    organization_id: text('organization_id').notNull(),
    site_id: text('site_id').notNull(),
    iot_device_id: text('iot_device_id').notNull(),
    created_at: text('created_at')
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
    updated_at: text('updated_at')
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index('idx_deployment_config_created_at').on(table.created_at),
    index('idx_deployment_config_updated_at').on(table.updated_at),
    index('idx_deployment_config_project_id').on(table.project_id),
    unique('unique_deployment_config_per_project').on(table.project_id),
  ]
)

type DrizzleDeploymentConfig = typeof deploymentConfig.$inferSelect
type DrizzleInsertDeploymentConfig = typeof deploymentConfig.$inferInsert

export type DeploymentConfig = DrizzleDeploymentConfig

export type InsertDeploymentConfig = DrizzleInsertDeploymentConfig

export type UpdateDeploymentConfig = Partial<
  Pick<DeploymentConfig, 'organization_id' | 'site_id' | 'iot_device_id'>
>
