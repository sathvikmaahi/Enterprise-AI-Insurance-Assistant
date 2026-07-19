const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`)
  }
  return response.json()
}
