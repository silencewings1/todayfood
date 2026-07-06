/**
 * useFortune - 今日宜吃核心逻辑（接入后端版）
 *
 * 数据来源：
 *   - GET  /api/fortune/today  获取今日食历 + 今日菜品（每日固定）
 *   - POST /api/fortune/draw   抽一道新菜（支持偏好）
 *
 * 本文件不再持有任何业务数据池，所有数据由后端返回。
 * 仅保留：状态管理、接口请求、分享文案拼接。
 */
import { ref, reactive, computed } from 'vue'

/* ===== 后端接口 ===== */
const API_TODAY = '/api/fortune/today'
const API_DRAW = '/api/fortune/draw'

/* ===== 全局状态 ===== */
const state = reactive({
  current: null,           // 当前菜品（今日菜品 或 开签后切换的菜品）
  locked: false,
  drawing: false,
  loaded: false,           // 当日数据是否已加载
  preferences: { mood: null, flavor: null, note: '' }
})

const today = ref({ text: '', short: '', week: '', seed: 0, date: '' })
const dailyExtras = ref(null)  // 今日食历内容（每日固定，不随开签变化）
let loadPromise = null         // 防止重复请求

/** 拉取今日食历 + 今日菜品（每日固定） */
async function loadToday() {
  if (loadPromise) return loadPromise
  loadPromise = (async () => {
    try {
      const res = await fetch(API_TODAY)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      today.value = data.today
      dailyExtras.value = data.extras
      // 仅在首次加载或被清空时设置 current，避免覆盖开签后的菜品
      if (!state.current) {
        state.current = data.todayFood
      }
      state.loaded = true
    } catch (e) {
      console.error('[useFortune] 加载今日食历失败:', e)
      throw e
    } finally {
      loadPromise = null
    }
  })()
  return loadPromise
}

/* ===== 抽签：请求后端 ===== */
async function fetchDrawResult() {
  const body = {
    excludeId: state.current?.id || null,
    preferences: { ...state.preferences }
  }
  const res = await fetch(API_DRAW, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  return data.food
}

/* ===== 全局 composable ===== */

/** 使用食历状态，首次调用会自动触发今日数据加载 */
export function useFortune() {
  // 首次调用时加载今日数据
  if (!state.loaded && !loadPromise) {
    loadToday()
  }

  const current = computed(() => state.current)
  const locked = computed(() => state.locked)
  const preferences = computed(() => state.preferences)

  /** 重抽（异步，带 drawing 状态锁） */
  async function redraw() {
    if (state.drawing) return state.current
    state.drawing = true
    state.locked = false
    try {
      const food = await fetchDrawResult()
      state.current = food
      return food
    } finally {
      state.drawing = false
    }
  }

  /** 按偏好抽（复用 redraw） */
  async function pickByPreference() {
    return redraw()
  }

  /** 锁定当前结果 */
  function lockResult() {
    state.locked = true
  }

  /** 重置偏好 */
  function resetPreferences() {
    state.preferences.mood = null
    state.preferences.flavor = null
    state.preferences.note = ''
  }

  /** 设置某个偏好 */
  function setPreference(group, value) {
    state.preferences[group] = value
  }

  /** 构建分享文案 */
  function buildShareText({ almanacYi, almanacJi, suitable, avoid, lucky, level }) {
    const f = state.current
    if (!f) return ''
    return `我的今日宜吃：${f.title}
今日食运：${level || f.level}
黄历宜：${almanacYi.join('、')}
黄历忌：${almanacJi.join('、')}
干饭宜：${suitable.join('、')}
干饭忌：${avoid.join('、')}
食神方位：${lucky.direction}｜幸运口味：${lucky.flavor}｜幸运颜色：${lucky.color}
「${f.sign}」`
  }

  return {
    today,
    state,
    current,
    locked,
    drawing: computed(() => state.drawing),
    preferences,
    dailyExtras,
    redraw,
    pickByPreference,
    lockResult,
    resetPreferences,
    setPreference,
    buildShareText,
    loadToday
  }
}
