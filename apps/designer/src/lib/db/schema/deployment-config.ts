import { sql } from 'drizzle-orm'
import { text, sqliteTable, index } from 'drizzle-orm/sqlite-core'

export const deploymentConfig = sqliteTable(
  'deployment_config',
  {
    id: text('id').primaryKey(),
    organization_id: text('organization_id').notNull(),
    site_id: text('site_id').notNull(),
    device_id: text('device_id').notNull(),
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
  ]
)

type DrizzleDeploymentConfig = typeof deploymentConfig.$inferSelect
type DrizzleInsertDeploymentConfig = typeof deploymentConfig.$inferInsert

export type DeploymentConfig = DrizzleDeploymentConfig

export type InsertDeploymentConfig = DrizzleInsertDeploymentConfig
