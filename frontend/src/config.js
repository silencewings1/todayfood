/**
 * 前端集中配置
 *
 * API 前缀从 .env 的 VITE_API_BASE 读取（默认 /api），
 * 路由路径作为与后端的契约在此集中声明，便于统一维护。
 *
 * 后端接口文档见 backend/README.md 与 http://localhost:8000/docs
 */

// API 前缀（开发环境由 vite 代理，生产环境由 nginx 反代）
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

/** 后端业务接口路径 */
export const API = {
  /** 今日食历 + 今日菜品 */
  TODAY: `${API_BASE}/fortune/today`,
  /** 抽一道新菜（POST，body: { excludeId, preferences }） */
  DRAW: `${API_BASE}/fortune/draw`,
}

export default { API }
