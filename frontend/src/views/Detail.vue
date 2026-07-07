<template>
  <div class="pick-view">
    <!-- 顶部固定栏 -->
    <AppHeader title="选一选" />

    <!-- 今日心情 -->
    <section class="page-section">
      <div class="card pick-card">
        <div class="title-row">
          <h3 class="card-title">今日心情</h3>
          <button class="btn-refresh" @click="refreshMood" aria-label="换一批">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
            <span>换</span>
          </button>
        </div>
        <div class="chip-row">
          <button
            v-for="opt in moodShown"
            :key="opt.value"
            class="chip"
            :class="{ active: prefs.mood === opt.value }"
            @click="onPick('mood', opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
    </section>

    <!-- 口味偏好 -->
    <section class="page-section">
      <div class="card pick-card">
        <div class="title-row">
          <h3 class="card-title">口味偏好</h3>
          <button class="btn-refresh" @click="refreshFlavor" aria-label="换一批">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
            <span>换</span>
          </button>
        </div>
        <div class="chip-row">
          <button
            v-for="opt in flavorShown"
            :key="opt.value"
            class="chip"
            :class="{ active: prefs.flavor === opt.value }"
            @click="onPick('flavor', opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
    </section>

    <!-- 想吃点啥（自定义，留给后端） -->
    <section class="page-section">
      <div class="card pick-card">
        <h3 class="card-title">想吃点啥</h3>
        <div class="note-wrap">
          <textarea
            class="note-input"
            v-model="noteText"
            placeholder="比如：热乎的汤面、别太油、想喝粥…"
            rows="2"
            maxlength="40"
          ></textarea>
          <span class="note-counter">{{ noteText.length }}/40</span>
        </div>
      </div>
    </section>

    <!-- 大按钮 -->
    <section class="page-section btn-row">
      <button
        class="btn-primary block-btn"
        :disabled="!canPick || drawing"
        @click="onPickMe"
      >
        {{ drawing ? '摇签中…' : (result ? '再选一餐' : '选一餐') }}
      </button>
    </section>

    <!-- 食神所选 结果卡 -->
    <section class="page-section" v-if="result">
      <div class="card result-card">
        <DrawOverlay :visible="showOverlay" @finished="onAnimFinished" />
        <div class="result-content" :class="{ hidden: showOverlay }">
          <div class="food-head">
            <span class="food-cat">{{ result.category }}</span>
            <span class="food-day">🍵 食神所选</span>
          </div>
          <h2 class="result-title">
            <span class="food-icon" v-html="foodSvg"></span>
            {{ result.title }}
          </h2>

          <!-- 星级 -->
          <div class="stars-row">
            <div class="stars-group">
              <span class="star-label">宜吃</span>
              <span class="stars">
                <span v-for="n in 5" :key="'y'+n" :class="['star', { on: n <= result.stars[0] }]">★</span>
              </span>
            </div>
            <div class="stars-group">
              <span class="star-label">开胃</span>
              <span class="stars">
                <span v-for="n in 5" :key="'k'+n" :class="['star', { on: n <= result.stars[1] }]">★</span>
              </span>
            </div>
            <div class="stars-group">
              <span class="star-label">治愈</span>
              <span class="stars">
                <span v-for="n in 5" :key="'z'+n" :class="['star', { on: n <= result.stars[2] }]">★</span>
              </span>
            </div>
          </div>

          <!-- 推荐理由 -->
          <div class="reason-block">
            {{ result.reason }}
          </div>

          <!-- 食神签文 -->
          <div class="sign-block">
            <div class="sign-head">{{ result.signName }} · {{ result.level }}</div>
            <div class="sign-quote">"{{ result.sign }}"</div>
          </div>

          <!-- 底部信息条 -->
          <div class="meta-row">
            <span class="meta-item">⏱ {{ result.cookTime }}</span>
            <span class="meta-dot">·</span>
            <span class="meta-item">🍳 {{ result.difficulty }}</span>
            <span class="meta-dot">·</span>
            <span class="meta-item">🧭 {{ result.direction }}</span>
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
    <RecipeSheet v-model:visible="showRecipe" :food="result" />

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

const { current, state, drawing, redraw } = useFortune()
const showOverlay = ref(false)
const showRecipe = ref(false)
let pendingRedraw = null

// 菜品 SVG 图标，无匹配时用 tomato-beef 兜底
const DEFAULT_FOOD_SVG = foodIcons['tomato-beef']
const foodSvg = computed(() => {
  const f = current.value
  return f ? (getFoodSvg(f.id) || DEFAULT_FOOD_SVG) : DEFAULT_FOOD_SVG
})

// 选项池（与菜品 tags 对应）
const moodPool = [
  { value: 'hungry', label: '饿极了' },
  { value: 'hungry', label: '饿到发慌' },
  { value: 'no-appetite', label: '没胃口' },
  { value: 'no-appetite', label: '没食欲' },
  { value: 'spicy', label: '想吃辣' },
  { value: 'spicy', label: '无辣不欢' },
  { value: 'treat', label: '犒劳下' },
  { value: 'treat', label: '想奖励自己' },
  { value: 'tired', label: '有点累' },
  { value: 'tired', label: '懒洋洋' },
  { value: 'happy', label: '心情好' },
  { value: 'happy', label: '开心' },
  { value: 'sad', label: '有点丧' },
  { value: 'sad', label: '情绪低落' },
  { value: 'busy', label: '赶时间' },
  { value: 'busy', label: '忙到飞起' }
]

const flavorPool = [
  { value: 'light', label: '清淡' },
  { value: 'light', label: '清爽' },
  { value: 'sour-sweet', label: '酸甜' },
  { value: 'sour-sweet', label: '糖醋' },
  { value: 'spicy', label: '微辣' },
  { value: 'spicy', label: '麻辣' },
  { value: 'heavy', label: '重口' },
  { value: 'heavy', label: '浓郁' },
  { value: 'savory', label: '咸鲜' },
  { value: 'savory', label: '酱香' },
  { value: 'milky', label: '奶香' },
  { value: 'milky', label: '芝士' },
  { value: 'sour-spicy', label: '酸辣' },
  { value: 'sour-spicy', label: '酸辣粉' },
  { value: 'fresh', label: '鲜美' },
  { value: 'fresh', label: '原味' }
]

// 从池子里随机抽 4 个（value 不重复，保证 4 个选项各不相同；允许跨次刷新部分重复）
function sampleFour(pool) {
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  const picked = []
  const seenValues = new Set()
  for (const opt of shuffled) {
    if (!seenValues.has(opt.value)) {
      picked.push(opt)
      seenValues.add(opt.value)
    }
    if (picked.length >= 4) break
  }
  return picked
}

const moodShown = ref(sampleFour(moodPool))
const flavorShown = ref(sampleFour(flavorPool))

function refreshMood() {
  moodShown.value = sampleFour(moodPool)
}
function refreshFlavor() {
  flavorShown.value = sampleFour(flavorPool)
}

const prefs = computed(() => state.preferences)
// 自定义输入：双向绑定到 state.preferences.note，后续传给后端
const noteText = computed({
  get: () => state.preferences.note || '',
  set: v => { state.preferences.note = v }
})
const canPick = computed(() => !!(prefs.value.mood || prefs.value.flavor || (prefs.value.note && prefs.value.note.trim())))
const result = computed(() => current.value)

function onPick(group, value) {
  if (state.preferences[group] === value) {
    state.preferences[group] = null
  } else {
    state.preferences[group] = value
  }
}

function onPickMe() {
  if (!canPick.value || drawing.value) return
  showOverlay.value = true
  // 并发发起抽签请求（redraw 内部已排除当前菜品，确保换新）
  pendingRedraw = redraw()
}

async function onAnimFinished() {
  if (pendingRedraw) {
    try { await pendingRedraw } catch (e) { /* 忽略，兜底保持旧值 */ }
    pendingRedraw = null
  }
  showOverlay.value = false
}
</script>

<style scoped>
.pick-view {
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

/* 标题行 + 刷新按钮 */
.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.title-row .card-title {
  margin: 0;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  min-height: 26px;
  padding: 0 10px;
  border-radius: var(--r-pill);
  background: var(--card-soft);
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 600;
  transition: transform 0.15s, background 0.2s;
}
.btn-refresh:active {
  transform: scale(0.92);
  background: var(--card-warm);
}
.btn-refresh svg {
  transition: transform 0.4s;
}
.btn-refresh:active svg {
  transform: rotate(-180deg);
}

/* ===== 选择卡 ===== */
.pick-card {
  padding: 14px 16px;
}

/* 结果卡（与首页菜品卡一致） */

/* 单行不换行：等分宽度 */
.chip-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
}

.chip {
  flex: 1;
  min-width: 0;
  min-height: 36px;
  padding: 0 6px;
  font-size: 0.86rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== 自定义输入框 ===== */
.note-wrap {
  position: relative;
}

.note-input {
  width: 100%;
  min-height: 56px;
  padding: 10px 12px 20px;
  border: 1.5px solid var(--rule);
  border-radius: 12px;
  background: var(--card);
  color: var(--ink);
  font-size: 0.9rem;
  line-height: 1.5;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
}
.note-input::placeholder {
  color: var(--ink-muted);
}
.note-input:focus {
  border-color: var(--accent);
}

.note-counter {
  position: absolute;
  right: 10px;
  bottom: 6px;
  font-size: 0.72rem;
  color: var(--ink-muted);
  pointer-events: none;
}

/* ===== 大按钮 ===== */
.btn-row {
  padding-top: 8px;
}

.block-btn {
  width: 100%;
  min-height: 46px;
  font-size: 1.05rem;
}

/* ===== 结果卡 ===== */
.result-card {
  position: relative;
  padding: 16px 18px;
}

.result-content {
  transition: opacity 0.2s;
}
.result-content.hidden {
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

.result-title {
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

/* 星级 */
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

/* 推荐理由 */
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

/* 签文 */
.sign-block {
  background: var(--card-warm);
  border-radius: 12px;
  padding: 10px 12px;
  text-align: center;
  margin-bottom: 10px;
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

/* 底部信息条 */
.meta-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--ink-soft);
  font-weight: 500;
}

.meta-dot {
  color: var(--rule-dashed);
}

/* 做法入口 */
.recipe-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: 12px;
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

.disclaimer {
  padding: 6px 0 2px;
  font-size: 0.72rem;
}
</style>
