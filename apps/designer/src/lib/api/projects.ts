import {
  Project,
  CreateProject,
  UpdateProject,
  ProjectQuery,
  ProjectListResponse,
  ProjectsResponseSchema,
  ProjectResponseSchema,
} from '@/app/api/projects/schemas'
import { withRetry, handleResponse } from './utils'

export const projectsApi = {
  async list(query?: ProjectQuery): Promise<ProjectListResponse> {
    const searchParams = new URLSearchParams()

    if (query?.page) searchParams.set('page', query.page.toString())
    if (query?.limit) searchParams.set('limit', query.limit.toString())
    if (query?.search) searchParams.set('search', query.search)
    if (query?.sort) searchParams.set('sort', query.sort)
    if (query?.order) searchParams.set('order', query.order)

    const url = `/api/projects${
      searchParams.toString() ? `?${searchParams}` : ''
    }`

    const result = await withRetry(async () => {
      const response = await fetch(url)
      return handleResponse(response)
    })

    const parsed = ProjectsResponseSchema.parse(result)

    if (!parsed.success || !parsed.data) {
      throw new Error(parsed.error || 'Failed to fetch projects')
    }

    return parsed.data
  },

  async get(id: string): Promise<Project> {
    const result = await withRetry(async () => {
      const response = await fetch(`/api/projects/${id}`)
      return handleResponse(response)
    })

    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success || !parsed.project) {
      throw new Error(parsed.error || 'Project not found')
    }

    return parsed.project
  },

  async create(data: CreateProject): Promise<Project> {
    const result = await withRetry(async () => {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      return handleResponse(response)
    })
    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success || !parsed.project) {
      throw new Error(parsed.error || 'Failed to create project')
    }

    return parsed.project
  },

  async update(id: string, data: UpdateProject): Promise<Project> {
    const result = await withRetry(async () => {
      const response = await fetch(`/api/projects/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      return handleResponse(response)
    })
    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success || !parsed.project) {
      throw new Error(parsed.error || 'Failed to update project')
    }

    return parsed.project
  },

  async delete(id: string): Promise<void> {
    const result = await withRetry(async () => {
      const response = await fetch(`/api/projects/${id}`, { method: 'DELETE' })
      return handleResponse(response)
    })
    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success) {
      throw new Error(parsed.error || 'Failed to delete project')
    }
  },
}
