<template>
  <div class="food-view">
    <!-- 顶部固定栏 -->
    <AppHeader :date-text="today.short" />

    <!-- 今日食历卡 -->
    <section class="page-section">
      <div class="calendar-card card">
        <!-- 宜栏 -->
        <div class="almanac-row">
          <div class="almanac-label">
            <div class="big-char yi">宜</div>
          </div>
          <div class="almanac-content">
            <div class="tag-group">
              <span class="tag-almanac" v-for="(item, i) in extras.almanacYi" :key="'ay'+i">{{ item }}</span>
            </div>
            <div class="tag-group">
              <span class="tag-food" v-for="(item, i) in extras.suitable" :key="'sy'+i">{{ item }}</span>
            </div>
          </div>
        </div>

        <div class="dashed-divider"></div>

        <!-- 忌栏 -->
        <div class="almanac-row">
          <div class="almanac-label">
            <div class="big-char ji">忌</div>
          </div>
          <div class="almanac-content">
            <div class="tag-group">
              <span class="tag-almanac" v-for="(item, i) in extras.almanacJi" :key="'aj'+i">{{ item }}</span>
            </div>
            <div class="tag-group">
              <span class="tag-food" v-for="(item, i) in extras.avoid.slice(0, 3)" :key="'sj'+i">{{ item }}</span>
            </div>
          </div>
        </div>

        <div class="dashed-divider"></div>
        <div class="pills-row">
          <span class="pill">幸运口味 · {{ extras.lucky.flavor }}</span>
          <span class="pill">食神方位 · {{ extras.lucky.direction }}</span>
        </div>
      </div>
    </section>

    <!-- 菜品卡 -->
    <section class="page-section" v-if="food">
      <div class="food-card card">
        <DrawOverlay :visible="showOverlay" @finished="onAnimFinished" />
        <div class="food-content" :class="{ hidden: showOverlay }">
          <div class="food-head">
            <span class="food-cat">{{ food.category }}</span>
            <span class="food-day">🍵 本日食历</span>
          </div>
          <h2 class="food-title">
            <span class="food-icon" v-html="foodSvg"></span>
            {{ food.title }}
          </h2>
          <div class="stars-row">
            <div class="stars-group">
              <span class="star-label">宜吃</span>
              <span class="stars">
                <span v-for="n in 5" :key="'y'+n" :class="['star', { on: n <= food.stars[0] }]">★</span>
              </span>
            </div>
            <div class="stars-group">
              <span class="star-label">开胃</span>
              <span class="stars">
                <span v-for="n in 5" :key="'k'+n" :class="['star', { on: n <= food.stars[1] }]">★</span>
              </span>
            </div>
            <div class="stars-group">
              <span class="star-label">治愈</span>
              <span class="stars">
                <span v-for="n in 5" :key="'z'+n" :class="['star', { on: n <= food.stars[2] }]">★</span>
              </span>
            </div>
          </div>
          <div class="reason-block">
            {{ food.reason }}
          </div>
          <div class="sign-block">
            <div class="sign-head">第 {{ extras.signNo }} 签 · {{ extras.signName }}</div>
            <div class="sign-quote">"{{ extras.signText }}"</div>
          </div>

          <!-- 做法入口 -->
          <button class="recipe-trigger" @click="showRecipe = true">
            <span class="recipe-trigger-text">看看怎么做</span>
            <span class="recipe-trigger-arrow">›</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 菜品做法 Bottom Sheet -->
    <RecipeSheet v-model:visible="showRecipe" :food="food" />

    <!-- 底部双按钮 -->
    <section class="page-section btn-row">
      <button class="btn-primary" style="flex:1" :disabled="drawing" @click="onRedraw">
        {{ drawing ? '摇签中…' : '再开一签' }}
      </button>
      <button class="btn-ghost" style="flex:1" :disabled="drawing" @click="onCopy">复制饭签</button>
    </section>

    <p class="disclaimer">娱乐参考，不代表真实预测 · 认真吃饭，开心最重要</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFortune } from '@/composables/useFortune'
import { getFoodSvg, foodIcons } from '@/data/icons'
import DrawOverlay from '@/components/DrawOverlay.vue'
import AppHeader from '@/components/AppHeader.vue'
import RecipeSheet from '@/components/RecipeSheet.vue'

const { today, current, dailyExtras, drawing, redraw, buildShareText } = useFortune()
const food = computed(() => current.value)
const showOverlay = ref(false)
const showRecipe = ref(false)
let pendingRedraw = null

// 菜品 SVG 图标，无匹配时用 tomato-beef 兜底
const DEFAULT_FOOD_SVG = foodIcons['tomato-beef']
const foodSvg = computed(() => {
  const f = food.value
  return f ? (getFoodSvg(f.id) || DEFAULT_FOOD_SVG) : DEFAULT_FOOD_SVG
})

const extras = computed(() => dailyExtras.value || {
  almanacYi: ['祈福', '出行', '开市'],
  almanacJi: ['嫁娶', '安葬'],
  suitable: ['换家没吃过的店', '少吃外卖多堂食', '热乎的就好'],
  avoid: ['为了省事跳过主食', '只喝奶茶不吃饭', '空腹灌冰美式'],
  lucky: { flavor: '清淡', color: '米白', direction: '那家总排队的店' },
  signNo: 54,
  signName: '随便改就它签',
  signLevel: '中吉',
  signText: '今日食签：中吉。适合把"随便"改成"就它"。'
})

async function onRedraw() {
  if (drawing.value) return
  showOverlay.value = true
  // 同时发起抽签请求（已预留后端接口），不阻塞动画
  pendingRedraw = redraw()
}

async function onAnimFinished() {
  // 动画结束时，确保数据已拿到（redraw 已经在 onRedraw 里并发发起）
  if (pendingRedraw) {
    try { await pendingRedraw } catch (e) { /* 忽略错误，兜底保持旧值 */ }
    pendingRedraw = null
  }
  showOverlay.value = false
}

function onCopy() {
  if (!food.value || !extras.value) return
  const text = buildShareText({
    almanacYi: extras.value.almanacYi,
    almanacJi: extras.value.almanacJi,
    suitable: extras.value.suitable,
    avoid: extras.value.avoid,
    lucky: extras.value.lucky,
    level: extras.value.signLevel
  })
  let ok = false
  try {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text)
      ok = true
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.cssText = 'position:fixed;opacity:0;'
      document.body.appendChild(ta)
      ta.select()
      ok = document.execCommand('copy')
      document.body.removeChild(ta)
    }
  } catch (e) { ok = false }
  showToast(ok ? '饭签已复制，快去召唤饭搭子～' : '复制失败，请手动长按复制')
}

function showToast(text) {
  const el = document.createElement('div')
  el.textContent = text
  el.style.cssText = `
    position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);
    background:rgba(42,20,8,0.92);color:#fff;padding:12px 22px;
    border-radius:14px;font-size:0.9rem;z-index:9999;pointer-events:none;
    animation:fadeIn 0.2s;
  `
  document.body.appendChild(el)
  setTimeout(() => {
    el.style.transition = 'opacity 0.3s'
    el.style.opacity = '0'
    setTimeout(() => el.remove(), 300)
  }, 1600)
}
</script>

<style scoped>
.food-view {
  min-height: 100%;
  padding-bottom: 4px;
}

/* ===== 区块 ===== */
.page-section {
  padding: 6px var(--pad-page);
}

.card-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--ink-strong);
  margin: 0 0 10px;
  letter-spacing: -0.02em;
}

/* ===== 今日食历卡 - 宜忌排版 ===== */
.calendar-card {
  position: relative;
  padding: 16px 18px;
}

.calendar-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 18px;
  right: 18px;
  height: 3px;
  background: linear-gradient(90deg, var(--accent-btn-start), var(--accent-btn-end));
  border-radius: 0 0 4px 4px;
}

.almanac-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.almanac-label {
  flex-shrink: 0;
  width: 34px;
  display: flex;
  justify-content: center;
  padding-top: 1px;
}

.big-char {
  font-size: 1.7rem;
  font-weight: 900;
  line-height: 1;
  letter-spacing: 0.05em;
}

.big-char.yi { color: var(--yi-color); }
.big-char.ji {
  color: var(--ji-color);
  text-decoration: line-through;
  text-decoration-color: rgba(196, 90, 46, 0.4);
  text-decoration-thickness: 2px;
}

.almanac-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-top: 2px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* 黄历标签：白底+细边框 */
.tag-almanac {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 5px;
  background: var(--card);
  border: 1px solid var(--rule);
  color: var(--ink);
  font-size: 0.78rem;
  font-weight: 500;
}

/* 干饭标签：暖底色 */
.tag-food {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 5px;
  background: var(--card-soft);
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 500;
}

.pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

/* ===== 菜品卡 ===== */
.food-card {
  position: relative;
  padding: 16px 18px;
}

.food-content {
  transition: opacity 0.2s;
}
.food-content.hidden {
  opacity: 0;
}

.food-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.food-cat {
  font-size: 0.82rem;
  color: var(--ink-soft);
  font-weight: 500;
}

.food-day {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 600;
}

.food-title {
  font-size: 1.7rem;
  font-weight: 900;
  color: var(--ink-strong);
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.food-icon {
  display: inline-flex;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}
.food-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.stars-row {
  display: flex;
  gap: 14px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.stars-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.star-label {
  font-size: 0.85rem;
  color: var(--ink);
  font-weight: 600;
}

.star {
  font-size: 15px;
  color: var(--rule);
}

.star.on {
  color: var(--accent);
}

.reason-block {
  background: var(--card-soft);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 0.9rem;
  color: var(--ink);
  line-height: 1.5;
  font-weight: 500;
  margin-bottom: 8px;
}

.sign-block {
  background: var(--card-warm);
  border-radius: 12px;
  padding: 10px 12px;
  text-align: center;
}

.sign-head {
  color: var(--ink-soft);
  font-size: 0.82rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.sign-quote {
  color: var(--ink);
  font-size: 0.88rem;
  line-height: 1.5;
  font-weight: 500;
}

/* 做法入口 */
.recipe-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: 10px;
  min-height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--card-soft), var(--card-warm));
  border: 1.5px solid var(--rule);
  color: var(--accent);
  font-size: 0.92rem;
  font-weight: 700;
  transition: transform 0.15s, border-color 0.2s;
}
.recipe-trigger:active {
  transform: scale(0.98);
  border-color: var(--accent-light);
}
.recipe-trigger-text {
  letter-spacing: -0.01em;
}
.recipe-trigger-arrow {
  font-size: 1.3rem;
  line-height: 1;
  color: var(--accent-light);
  font-weight: 400;
}

/* ===== 双按钮 ===== */
.btn-row {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.btn-row :deep(.btn-primary),
.btn-row :deep(.btn-ghost) {
  min-height: 46px;
  font-size: 1.05rem;
}

.disclaimer {
  padding: 6px 0 2px;
  font-size: 0.72rem;
}
</style>
