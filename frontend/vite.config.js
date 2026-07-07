import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
// 端口与代理目标从 .env 读取（VITE_DEV_PORT / VITE_DEV_PROXY_TARGET）
// 详见 frontend/.env.example
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devPort = parseInt(env.VITE_DEV_PORT || '5173', 10)
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      host: '0.0.0.0',
      port: devPort,
      open: false,
      // 代理 /api 到后端 FastAPI（地址由 VITE_DEV_PROXY_TARGET 配置）
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false
    }
  }
})
