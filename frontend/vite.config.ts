import path from 'node:path'
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // The Recharts-backed chart tests render a full SVG in jsdom, which takes
    // well over the 5s default on a slower machine and fails the pre-commit
    // hook for reasons that have nothing to do with the code under test. A
    // higher ceiling costs a fast test nothing — it only stops a slow one
    // being reported as broken.
    testTimeout: 20000,
    // Vitest loads .env files through Vite, so a developer's local backend
    // config would otherwise leak in and change what the app fetches under
    // test. Pin these empty; tests that need them stub explicitly.
    env: {
      VITE_API_BASE_URL: '',
      VITE_ALERT_API_BASE_URL: '',
      VITE_PRICE_WS_URL: '',
      VITE_NOTIFICATION_STREAM_URL: '',
    },
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/e2e/**',
      '**/.{idea,git,cache,output,temp}/**',
    ],
  },
})
