// Public entrypoint for the typed API client.
//
// The generated SDK (src/api/generated) is produced from the backend's
// OpenAPI schema by @hey-api/openapi-ts — do not edit it by hand; run
// `pnpm generate:api` to refresh it.
//
// Here we configure the shared client instance once, then re-export the
// generated SDK functions and types for the rest of the app to use.
import { client } from './generated/client.gen'

// Request URLs already include the `/api` prefix, so an empty base URL means
// requests are same-origin (proxied to Django by Vite in dev). In production,
// set VITE_API_BASE_URL to the API origin, e.g. https://api.example.com
client.setConfig({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  // Send the Django session & CSRF cookies with every request. Required for
  // session-cookie authentication (works cross-origin thanks to
  // CORS_ALLOW_CREDENTIALS on the backend).
  credentials: 'include',
})

// Read a cookie value by name (used for Django's CSRF token).
function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

// Django enforces CSRF on unsafe methods for session-authenticated requests.
// Echo the `csrftoken` cookie back in the X-CSRFToken header. Call
// `authCsrfRetrieve()` once on app start to make sure the cookie is set.
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE'])
client.interceptors.request.use((request) => {
  if (!SAFE_METHODS.has(request.method.toUpperCase())) {
    const token = getCookie('csrftoken')
    if (token) request.headers.set('X-CSRFToken', token)
  }
  return request
})

export * from './generated'
