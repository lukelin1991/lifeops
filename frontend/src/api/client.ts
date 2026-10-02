// Small typed wrapper around fetch.
// - Base URL from VITE_API_URL (falls back to http://localhost:8000)
// - Attaches the JWT (if logged in) as "Authorization: Bearer ..."
// - Turns FastAPI error responses into ApiError with a readable message

export const API_URL = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
).replace(/\/+$/, '')

const TOKEN_KEY = 'lifeops.token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

// Fired when the API says our token is missing/expired, so the
// auth provider can send the user back to the login page.
export const UNAUTHORIZED_EVENT = 'lifeops:unauthorized'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

type Query = Record<string, string | number | boolean | null | undefined>

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Query
}

function buildUrl(path: string, query?: Query) {
  const url = new URL(`${API_URL}${path}`)

  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value))
    }
  }

  return url.toString()
}

// FastAPI errors look like {"detail": "text"} or, for validation
// errors, {"detail": [{"loc": [...], "msg": "..."}]}.
function errorMessage(data: unknown): string {
  if (data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail

    if (typeof detail === 'string') return detail

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item: { loc?: unknown[]; msg?: string }) => {
          const field = item.loc?.slice(1).join('.')
          return field ? `${field}: ${item.msg}` : item.msg
        })
        .join('; ')
    }
  }

  return 'Something went wrong'
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {}
  const token = getToken()

  if (token) headers.Authorization = `Bearer ${token}`
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response

  try {
    response = await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body:
        options.body !== undefined
          ? JSON.stringify(options.body)
          : undefined,
    })
  } catch {
    throw new ApiError(0, 'Could not connect to the LifeOps API.')
  }

  let data: unknown
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      setToken(null)
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    }

    throw new ApiError(response.status, errorMessage(data))
  }

  return data as T
}

export const api = {
  get: <T>(path: string, query?: Query) =>
    apiRequest<T>(path, { query }),
  post: <T>(path: string, body?: unknown, query?: Query) =>
    apiRequest<T>(path, { method: 'POST', body, query }),
  patch: <T>(path: string, body: unknown) =>
    apiRequest<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) =>
    apiRequest<T>(path, { method: 'DELETE' }),
}

// Most endpoints wrap results as {"data": ..., "message": ...}
export type Envelope<T> = {
  data: T
  message?: string
}

export function describeError(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Something went wrong'
}
