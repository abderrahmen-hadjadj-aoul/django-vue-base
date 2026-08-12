import { defineConfig } from '@hey-api/openapi-ts'

// Generates the typed API client from the backend's OpenAPI schema.
// Regenerate with: pnpm generate:api
// (run `python manage.py spectacular --format openapi-json --file openapi.json`
// in ../backend first to refresh the schema).
export default defineConfig({
  input: '../backend/openapi.json',
  output: {
    path: 'src/api/generated',
  },
  plugins: [
    '@hey-api/client-fetch',
    '@hey-api/sdk',
    '@hey-api/typescript',
  ],
})
