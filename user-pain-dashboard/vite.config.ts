import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// 部署到 GitHub Pages 时 base 路径通过环境变量 VITE_BASE 指定。
// 本地开发用 "/"，CI 构建时由 workflow 注入 "/<repo>/"。
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  return {
    plugins: [react()],
    base: env.VITE_BASE || '/',
    server: {
      host: '0.0.0.0',
      allowedHosts: true,
    },
  }
})
