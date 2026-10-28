
const API_BASE = '/api'

export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE}/health`)

  if (!response.ok) {
    throw new Error(`Backend request failed: ${response.status}`)
  }

  return response.json() as Promise<{
    status: string
    message: string
  }>
}
