import { sql } from 'drizzle-orm'
import { text, sqliteTable, index } from 'drizzle-orm/sqlite-core'

export const projects = sqliteTable(
  'projects',
  {
    id: text('id').primaryKey(),
    name: text('name').notNull(),
    description: text('description'),
    flow_config: text('flow_config').notNull().default('{}'),
    created_at: text('created_at')
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
    updated_at: text('updated_at')
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index('idx_projects_created_at').on(table.created_at),
    index('idx_projects_updated_at').on(table.updated_at),
  ]
)

// Base types from Drizzle
type DrizzleProject = typeof projects.$inferSelect
type DrizzleNewProject = typeof projects.$inferInsert

// Mapped types to match bms-schemas (null -> undefined)
export type Project = Omit<DrizzleProject, 'description'> & {
  description?: string | undefined
}

export type NewProject = Omit<DrizzleNewProject, 'description'> & {
  description?: string | undefined
}
