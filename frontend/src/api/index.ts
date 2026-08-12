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
})

export * from './generated'
