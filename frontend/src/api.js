// Tiny fetch wrapper around the Django REST API.
// In development, requests to /api are proxied to the backend by Vite
// (see vite.config.js). In production, set VITE_API_BASE_URL to the API origin.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`)
  }
  return response.status === 204 ? null : response.json()
}

export const api = {
  health: () => request('/health/'),
  listItems: () => request('/items/'),
  createItem: (data) =>
    request('/items/', { method: 'POST', body: JSON.stringify(data) }),
}
