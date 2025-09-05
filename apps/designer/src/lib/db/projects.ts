import 'server-only'

import { eq, like, or, asc, desc, count } from 'drizzle-orm'
import { getDatabase } from './client'
import { projects, type Project } from './schema'
import {
  CreateProject,
  UpdateProject,
  ProjectQuery,
  ProjectListResponse,
} from '@/app/api/projects/schemas'
import { randomUUID } from 'crypto'

export class ProjectsRepository {
  private get db() {
    return getDatabase()
  }

  // Create a new project
  create(data: CreateProject): Project {
    const id = randomUUID()
    const now = new Date().toISOString()
    const flowConfig = JSON.stringify(data.flow_config || {})

    const newProject = {
      id,
      name: data.name,
      description: data.description || null,
      flow_config: flowConfig,
      created_at: now,
      updated_at: now,
    }

    const result = this.db.insert(projects).values(newProject).returning().get()
    return {
      ...result,
      description: result.description ?? undefined,
    }
  }

  // Find project by ID
  findById(id: string): Project | null {
    const result = this.db
      .select()
      .from(projects)
      .where(eq(projects.id, id))
      .get()

    if (!result) return null

    return {
      ...result,
      description: result.description ?? undefined,
    }
  }

  // Update project
  update(id: string, data: UpdateProject): Project | null {
    const existing = this.findById(id)
    if (!existing) return null

    const updateData: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    }

    if (data.name !== undefined) {
      updateData.name = data.name
    }

    if (data.description !== undefined) {
      updateData.description = data.description || null
    }

    if (data.flow_config !== undefined) {
      updateData.flow_config = JSON.stringify(data.flow_config)
    }

    const result = this.db
      .update(projects)
      .set(updateData)
      .where(eq(projects.id, id))
      .returning()
      .get()

    if (!result) return null

    return {
      ...result,
      description: result.description ?? undefined,
    }
  }

  // Delete project
  delete(id: string): boolean {
    const result = this.db.delete(projects).where(eq(projects.id, id)).run()

    return result.changes > 0
  }

  // List projects with pagination and search
  list(query: Partial<ProjectQuery> = {}): ProjectListResponse {
    const {
      page = 1,
      limit = 20,
      search,
      sort = 'updated_at',
      order = 'desc',
    } = query
    const offset = (page - 1) * limit

    // Build where clause for search
    let whereClause = undefined
    if (search) {
      whereClause = or(
        like(projects.name, `%${search}%`),
        like(projects.description, `%${search}%`)
      )
    }

    // Build order clause
    const validSorts = ['name', 'created_at', 'updated_at'] as const
    type ValidSort = (typeof validSorts)[number]
    const isValidSort = (s: string | null): s is ValidSort =>
      s !== null && validSorts.includes(s as ValidSort)
    const sortColumn = isValidSort(sort) ? sort : 'updated_at'
    const orderFn = order === 'asc' ? asc : desc
    const orderClause = orderFn(projects[sortColumn])

    // Get total count
    const totalResult = this.db
      .select({ count: count() })
      .from(projects)
      .where(whereClause)
      .get()

    const total = totalResult?.count || 0

    // Get projects
    const query_builder = this.db.select().from(projects)

    const query_with_conditions = whereClause
      ? query_builder.where(whereClause)
      : query_builder

    const projectsList = query_with_conditions
      .orderBy(orderClause)
      .limit(limit)
      .offset(offset)
      .all()

    const pages = Math.ceil(total / limit)

    // Map null to undefined for description field to match schema
    const mappedProjects = projectsList.map((project) => ({
      ...project,
      description: project.description ?? undefined,
    }))

    return {
      projects: mappedProjects,
      total,
      page,
      limit,
      pages,
    }
  }

  // Check if project exists
  exists(id: string): boolean {
    const result = this.db
      .select({ count: count() })
      .from(projects)
      .where(eq(projects.id, id))
      .get()

    return (result?.count || 0) > 0
  }

  // Get project count
  count(): number {
    const result = this.db.select({ count: count() }).from(projects).get()

    return result?.count || 0
  }

  // Search projects by name
  searchByName(name: string): Project[] {
    const results = this.db
      .select()
      .from(projects)
      .where(like(projects.name, `%${name}%`))
      .orderBy(asc(projects.name))
      .all()

    return results.map((result) => ({
      ...result,
      description: result.description ?? undefined,
    }))
  }
}

// Export singleton instance
export const projectsRepository = new ProjectsRepository()
