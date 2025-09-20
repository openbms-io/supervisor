import 'server-only'

import { eq, like, or, asc, desc } from 'drizzle-orm'
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
  async create(data: CreateProject): Promise<Project> {
    const id = randomUUID()
    const now = new Date().toISOString()
    const workflowConfig = JSON.stringify(data.workflow_config || {})

    const newProject = {
      id,
      name: data.name,
      description: data.description || null,
      workflow_config: workflowConfig,
      created_at: now,
      updated_at: now,
    }

    // Insert then fetch by id to keep compatibility across drivers
    await this.db.insert(projects).values(newProject).run()

    const fetched = await this.db
      .select()
      .from(projects)
      .where(eq(projects.id, id))
      .get()

    const result = fetched!
    return {
      ...result,
      description: result.description ?? undefined,
    }
  }

  // Find project by ID
  async findById(id: string): Promise<Project | null> {
    const result = await this.db
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
  async update(id: string, data: UpdateProject): Promise<Project | null> {
    const existing = await this.findById(id)
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

    if (data.workflow_config !== undefined) {
      updateData.workflow_config = JSON.stringify(data.workflow_config)
    }

    await this.db
      .update(projects)
      .set(updateData)
      .where(eq(projects.id, id))
      .run()

    const result = await this.db
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

  // Delete project
  async delete(id: string): Promise<boolean> {
    // Check existence first for consistent behavior
    const existed = await this.exists(id)
    if (!existed) return false

    await this.db.delete(projects).where(eq(projects.id, id)).run()
    return true
  }

  // List projects with pagination and search
  async list(query: Partial<ProjectQuery> = {}): Promise<ProjectListResponse> {
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

    // Get total count (avoid select fields to satisfy both drivers)
    const totalBase = this.db.select().from(projects)
    const totalQuery = whereClause ? totalBase.where(whereClause) : totalBase
    const totalRows = await totalQuery.all()
    const total = totalRows.length

    // Get projects
    const query_builder = this.db.select().from(projects)

    const query_with_conditions = whereClause
      ? query_builder.where(whereClause)
      : query_builder

    const projectsList = await query_with_conditions
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
  async exists(id: string): Promise<boolean> {
    const result = await this.db
      .select()
      .from(projects)
      .where(eq(projects.id, id))
      .get()

    return !!result
  }

  // Get project count
  async count(): Promise<number> {
    const rows = await this.db.select().from(projects).all()
    return rows.length
  }

  // Search projects by name
  async searchByName(name: string): Promise<Project[]> {
    const results = await this.db
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
