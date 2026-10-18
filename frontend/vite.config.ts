import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const rawTarget = env.VITE_API_URL?.trim() || 'http://127.0.0.1:8000'
  // Remove /api suffix if someone put full endpoint into VITE_API_URL
  const target = rawTarget.replace(/\/api\/?$/, '').replace(/\/+$/, '') || 'http://127.0.0.1:8000'

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: target,
          changeOrigin: true,
        },
      },
    },
  }
})
