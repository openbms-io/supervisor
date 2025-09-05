import {
  Project,
  CreateProject,
  UpdateProject,
  ProjectQuery,
  ProjectListResponse,
  ProjectsResponseSchema,
  ProjectResponseSchema,
} from '@/app/api/projects/schemas'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: Response
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text()
    throw new ApiError(
      response.status,
      `API Error: ${response.status} ${text}`,
      response
    )
  }

  return response.json()
}

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

    const response = await fetch(url)
    const result = await handleResponse(response)

    const parsed = ProjectsResponseSchema.parse(result)

    if (!parsed.success || !parsed.data) {
      throw new Error(parsed.error || 'Failed to fetch projects')
    }

    return parsed.data
  },

  async get(id: string): Promise<Project> {
    const response = await fetch(`/api/projects/${id}`)
    const result = await handleResponse(response)

    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success || !parsed.project) {
      throw new Error(parsed.error || 'Project not found')
    }

    return parsed.project
  },

  async create(data: CreateProject): Promise<Project> {
    const response = await fetch('/api/projects', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    const result = await handleResponse(response)
    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success || !parsed.project) {
      throw new Error(parsed.error || 'Failed to create project')
    }

    return parsed.project
  },

  async update(id: string, data: UpdateProject): Promise<Project> {
    const response = await fetch(`/api/projects/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    const result = await handleResponse(response)
    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success || !parsed.project) {
      throw new Error(parsed.error || 'Failed to update project')
    }

    return parsed.project
  },

  async delete(id: string): Promise<void> {
    const response = await fetch(`/api/projects/${id}`, {
      method: 'DELETE',
    })

    const result = await handleResponse(response)
    const parsed = ProjectResponseSchema.parse(result)

    if (!parsed.success) {
      throw new Error(parsed.error || 'Failed to delete project')
    }
  },
}
