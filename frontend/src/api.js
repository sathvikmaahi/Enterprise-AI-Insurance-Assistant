// Empty in local dev → Vite proxies to http://127.0.0.1:8000 (see vite.config.js).
// Set VITE_API_BASE_URL only when the UI is not served by Vite (e.g. static hosting).
const configured = import.meta.env.VITE_API_BASE_URL
const API_BASE =
  typeof configured === 'string' && configured.trim() !== ''
    ? configured.replace(/\/$/, '')
    : ''

export class ApiError extends Error {
  constructor(status, detail, reason = null) {
    super(typeof detail === 'string' ? detail : detail?.detail || 'Request failed')
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.reason = reason ?? detail?.reason ?? null
  }
}

async function parseError(response) {
  let body = null
  try {
    body = await response.json()
  } catch {
    body = null
  }
  const detail = body?.detail ?? body ?? response.statusText
  const nested = typeof detail === 'object' ? detail : { detail }
  return new ApiError(
    response.status,
    nested.detail ?? nested,
    nested.reason ?? null,
  )
}

async function request(path, { method = 'GET', token, body } = {}) {
  const headers = {}
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    const hint = API_BASE
      ? `Cannot reach ${API_BASE}${path}. Is FastAPI on :8000?`
      : `Cannot reach ${path} (Vite → 127.0.0.1:8000). Is FastAPI running?`
    const cause = err instanceof Error && err.message ? ` (${err.message})` : ''
    throw new ApiError(0, `${hint}${cause}`)
  }

  if (!response.ok) {
    throw await parseError(response)
  }
  if (response.status === 204) {
    return null
  }
  return response.json()
}

export async function getHealth() {
  return request('/health')
}

export async function login(username, password) {
  return request('/auth/login', {
    method: 'POST',
    body: { username, password },
  })
}

export async function ask(question, token) {
  return request('/ask', {
    method: 'POST',
    token,
    body: { question },
  })
}

export async function getLogs(token, limit = 50) {
  return request(`/logs?limit=${limit}`, { token })
}
