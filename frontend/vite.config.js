import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api calls to the FastAPI backend
      // so the browser never gets a CORS error in dev mode
      '/health':    { target: 'http://localhost:8000', changeOrigin: true },
      '/chat':      { target: 'http://localhost:8000', changeOrigin: true },
      '/rag':       { target: 'http://localhost:8000', changeOrigin: true },
      '/sql':       { target: 'http://localhost:8000', changeOrigin: true },
      '/eval':      { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
