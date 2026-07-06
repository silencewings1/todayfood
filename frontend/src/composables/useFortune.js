/**
 * useFortune - 今日宜吃核心逻辑
 * 包含：日期种子、抽签、个性化匹配、忌吃/宜吃/幸运三件套生成
 */
import { ref, reactive, computed } from 'vue'
import { foodPool } from '@/data/foods'
import { signPool, pickSign as pickSignFromPool } from '@/data/signs'
import { avoidPool } from '@/data/avoids'
import { suitablePool } from '@/data/suitable'
import { pickAlmanacYi, pickAlmanacJi } from '@/data/almanac'

/* ===== 日期 / 种子 ===== */
export function todayInfo() {
  const d = new Date()
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  const day = d.getDate()
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return {
    text: `${y} 年 ${m} 月 ${day} 日 · 周${week}`,
    short: `${m} 月 ${day} 日`,
    week,
    seed: y * 10000 + m * 100 + day
  }
}

/** 基于种子的伪随机数生成器（LCG） */
export function seededRandom(seed) {
  let s = seed
  return function () {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

/* ===== 选择逻辑 ===== */

/** 根据个性化标签加权打分，挑出最匹配的菜品（使用 mood + flavor；note 留给后端） */
export function pickByTags(prefs, saltSeed = null) {
  const seed = saltSeed ?? (todayInfo().seed + Date.now() % 1000)
  const rand = seededRandom(seed)
  const scored = foodPool.map(f => {
    let score = 0
    if (prefs.mood && f.tags.mood.includes(prefs.mood)) score += 3
    if (prefs.flavor && f.tags.flavor.includes(prefs.flavor)) score += 3
    score += rand() * 1.2
    return { f, score }
  })
  scored.sort((a, b) => b.score - a.score)
  return scored[0].f
}

/** 完全随机挑一个菜品（可排除指定菜品） */
export function pickAny(exclude = null) {
  const pool = exclude ? foodPool.filter(f => f.id !== exclude.id) : foodPool
  const idx = Math.floor(Math.random() * pool.length)
  return pool[idx]
}

/** 按日期种子挑"今日固定"菜品（每天稳定） */
export function pickTodayFood() {
  const seed = todayInfo().seed
  const rand = seededRandom(seed)
  const idx = Math.floor(rand() * foodPool.length)
  return foodPool[idx]
}

/** 选今日宜吃组（3 条） */
export function pickSuitable(seed) {
  const rand = seededRandom(seed)
  return suitablePool[Math.floor(rand() * suitablePool.length)]
}

/** 选今日忌吃清单（3-5 条） */
export function pickAvoid(seed) {
  const rand = seededRandom(seed + 17)
  const count = 3 + Math.floor(rand() * 2)
  const shuffled = [...avoidPool].sort(() => rand() - 0.5)
  return shuffled.slice(0, count)
}

/** 选今日幸运三件套（口味 / 幸运色 / 食神方位-趣味描述） */
export function pickLucky(seed) {
  const rand = seededRandom(seed + 31)
  const flavors = ['微辣', '清淡', '酸甜', '奶香', '酱香', '麻辣', '酸辣', '原味', '咸鲜', '甘甜']
  const colors = ['暖橙', '正红', '薄荷绿', '麦黄', '米白', '姜黄', '焦糖', '番茄红']
  const directions = [
    '那家总排队的店',
    '楼下走两步那家',
    '常点的那家老店',
    '朋友推荐过的新店',
    '外卖好评榜首位',
    '出地铁左拐那家',
    '公司食堂三楼',
    '冰箱里剩下的菜',
    '巷口藏着的小摊',
    '家里的厨房'
  ]
  return {
    flavor: flavors[Math.floor(rand() * flavors.length)],
    color: colors[Math.floor(rand() * colors.length)],
    direction: directions[Math.floor(rand() * directions.length)]
  }
}

/** 抽签编号（1-99 之间，按种子稳定） */
export function pickSignNo(seed) {
  return 1 + Math.floor(((seed * 7) % 233280) / 233280 * 99)
}

/** 抽一支签（返回 { name, level, text }） */
export function pickSignObj(seed) {
  return pickSignFromPool(seed)
}

/* ===== 全局状态 composable ===== */
const state = reactive({
  current: null,
  locked: false,
  drawing: false,
  preferences: { mood: null, flavor: null, note: '' }
})

const today = todayInfo()

/** 初始化默认推荐 */
export function useFortune() {
  // 如果还没初始化，按今日种子挑一个
  if (!state.current) {
    state.current = pickTodayFood()
  }

  const current = computed(() => state.current)
  const locked = computed(() => state.locked)
  const preferences = computed(() => state.preferences)

  /**
   * 派生数据：宜吃/忌吃/幸运三件套/签号/签文
   * 全部基于 today.seed 稳定生成，"今日食历"每日固定不变；
   * 开签只换 state.current（菜品），不影响本卡内容。
   */
  const dailyExtras = computed(() => {
    const f = state.current
    if (!f) return null
    const signObj = pickSignObj(today.seed)
    return {
      almanacYi: pickAlmanacYi(today.seed),
      almanacJi: pickAlmanacJi(today.seed),
      suitable: pickSuitable(today.seed),
      avoid: pickAvoid(today.seed),
      lucky: pickLucky(today.seed),
      signNo: pickSignNo(today.seed),
      signName: signObj.name,
      signLevel: signObj.level,
      signText: signObj.text
    }
  })

  /**
   * 向后端请求新签结果（接入后端时替换此函数）
   * TODO: 接入后端 API，例如：
   *   const res = await fetch('/api/fortune/draw', { method: 'POST', body: JSON.stringify({ prefs: state.preferences }) })
   *   return await res.json()
   * 当前走本地兜底：随机挑一个菜品。
   */
  async function fetchDrawResult() {
    // 模拟一点网络延迟（0.3~0.9s），让动画自然；接入真实后端时可删除
    await new Promise(r => setTimeout(r, 300 + Math.random() * 600))
    const prefs = state.preferences
    const haveAny = Object.values(prefs).some(v => v)
    // 排除当前菜品，确保每次"再开一签"都会切换
    const current = state.current
    let result
    if (haveAny) {
      // 用当前时间作为盐，保证每次调用结果不同
      result = pickByTags(prefs, todayInfo().seed + Date.now())
      // 兜底：如果选出来的和当前一样，随机挑一个不同的
      if (current && result.id === current.id) {
        result = pickAny(current)
      }
    } else {
      result = pickAny(current)
    }
    return result
  }

  /** 重抽（异步，带 drawing 状态锁；预留后端调用） */
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

  /** 按偏好抽（复用 redraw 逻辑，保持一致） */
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
    buildShareText
  }
}
