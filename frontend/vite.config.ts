import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // Don't let the dev server's file watcher react to e2e test artifacts. The
    // suite runs against this very server while playwright-bdd writes generated
    // specs (.features-gen/) and Playwright writes its report/results; without
    // this, each write triggers a full page reload that wipes app state
    // mid-scenario and fails the tests.
    watch: {
      ignored: ['**/.features-gen/**', '**/playwright-report/**', '**/test-results/**'],
    },
    // Proxy API calls to the Django backend during development so the
    // frontend can use same-origin relative URLs (e.g. fetch('/api/health/')).
    // The target is overridable so the e2e run can point at its own backend
    // (port 8001, dedicated SQLite DB) instead of the dev server on :8000.
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
