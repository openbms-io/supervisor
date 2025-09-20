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

async function withRetry<T>(
  fn: () => Promise<T>,
  opts?: { attempts?: number; baseDelayMs?: number; factor?: number }
): Promise<T> {
  const attempts = opts?.attempts ?? 3
  const baseDelay = opts?.baseDelayMs ?? 200
  const factor = opts?.factor ?? 2
  let lastErr: unknown
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      if (i < attempts - 1) {
        const delay = baseDelay * Math.pow(factor, i)
        await new Promise((res) => setTimeout(res, delay))
        continue
      }
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error('Request failed')
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
