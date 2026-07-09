/**
 * 前端集中配置
 *
 * API 前缀从 .env 的 VITE_API_BASE 读取，
 * 生产环境默认 /projects/todayfood/api（由 nginx 反代到 FastAPI），
 * 开发环境默认 /api（由 vite 代理到 FastAPI）。
 *
 * 路由路径作为与后端的契约在此集中声明，便于统一维护。
 * 后端接口文档见 backend/README.md 与 http://localhost:8000/docs
 */

// API 前缀
const API_BASE = import.meta.env.VITE_API_BASE || (import.meta.env.PROD ? '/projects/todayfood/api' : '/api')

/** 后端业务接口路径 */
export const API = {
  /** 今日食历 + 今日菜品 */
  TODAY: `${API_BASE}/fortune/today`,
  /** 抽一道新菜（POST，body: { excludeId, preferences }） */
  DRAW: `${API_BASE}/fortune/draw`,
}

/**
 * 摇签动画最短总时长（毫秒）
 * 不管走不走 AI 调用，摇签动画至少持续这么久；
 * 若 AI 调用耗时更长，则摇动状态会一直保持到后端返回。
 */
export const DRAW_MIN_DURATION = 2500

export default { API, DRAW_MIN_DURATION }
