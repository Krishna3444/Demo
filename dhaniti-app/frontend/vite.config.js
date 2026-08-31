import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend port can be overridden for local setups, e.g.:
//   API_PROXY_TARGET=http://localhost:5000 npm run dev
const proxyTarget = process.env.API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': proxyTarget,
      '/auth': proxyTarget,
    },
  },
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
