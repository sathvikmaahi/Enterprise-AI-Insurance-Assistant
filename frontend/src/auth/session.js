const STORAGE_KEY = 'insurance_assistant_session'

export function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.access_token || !parsed?.role || !parsed?.username) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function saveSession(session) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY)
}
