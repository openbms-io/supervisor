export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: Response
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function handleResponse<T>(response: Response): Promise<T> {
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

export async function withRetry<T>(
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
