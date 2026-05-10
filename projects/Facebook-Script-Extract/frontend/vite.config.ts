import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/fbse/',
  server: {
    port: 5173,
    proxy: {
      '/fbse/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/fbse\/api/, ''),
      },
      '/fbse/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/fbse\/ws/, '/ws'),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
