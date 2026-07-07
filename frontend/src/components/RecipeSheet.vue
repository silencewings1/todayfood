<template>
  <transition name="sheet">
    <div v-if="visible" class="sheet-mask" @click.self="onClose" @touchmove.prevent>
      <div class="sheet-body" @click.stop>
        <!-- 拖拽条 -->
        <div class="sheet-handle"></div>

        <!-- 标题栏 -->
        <div class="sheet-head">
          <div class="sheet-title">
            <span class="food-icon" v-html="foodSvg"></span>
            <span>{{ food?.title || '做法' }}</span>
          </div>
          <button class="sheet-close" @click="onClose" aria-label="关闭">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
          </button>
        </div>

        <!-- 概览条 -->
        <div class="meta-bar">
          <span class="meta-pill"><i class="meta-dot"></i>时长 {{ food?.cookTime || '-' }}</span>
          <span class="meta-pill"><i class="meta-dot"></i>难度 {{ food?.difficulty || '-' }}</span>
          <span class="meta-pill" v-if="food?.direction"><i class="meta-dot"></i>方位 {{ food.direction }}</span>
        </div>

        <!-- 内容区（可滚动） -->
        <div class="sheet-scroll" @touchmove.stop>
          <!-- 食材 -->
          <section v-if="food?.ingredients?.length" class="recipe-section">
            <h4 class="section-title">食材</h4>
            <ul class="ingredient-list">
              <li v-for="(item, i) in food.ingredients" :key="i">
                <span class="ing-dot"></span>
                <span>{{ item }}</span>
              </li>
            </ul>
          </section>

          <!-- 步骤 -->
          <section v-if="food?.steps?.length" class="recipe-section">
            <h4 class="section-title">步骤</h4>
            <ol class="step-list">
              <li v-for="(step, i) in food.steps" :key="i">
                <span class="step-num">{{ i + 1 }}</span>
                <p>{{ step }}</p>
              </li>
            </ol>
          </section>

          <!-- 小贴士 -->
          <section v-if="food?.tip" class="recipe-section">
            <h4 class="section-title">小贴士</h4>
            <div class="tip-block">
              <p>{{ food.tip }}</p>
            </div>
          </section>

          <div class="sheet-foot-gap"></div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, watch } from 'vue'
import { getFoodSvg, foodIcons } from '@/data/icons'

const props = defineProps({
  visible: { type: Boolean, default: false },
  food: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'close'])

const DEFAULT_SVG = foodIcons['tomato-beef']
const foodSvg = computed(() => {
  const f = props.food
  return f ? (getFoodSvg(f.id) || DEFAULT_SVG) : DEFAULT_SVG
})

function onClose() {
  emit('update:visible', false)
  emit('close')
}

// 打开时锁定 body 滚动
watch(() => props.visible, (v) => {
  if (typeof document !== 'undefined') {
    document.body.style.overflow = v ? 'hidden' : ''
  }
})
</script>

<style scoped>
.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(26, 10, 2, 0.5);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  -webkit-tap-highlight-color: transparent;
}

.sheet-body {
  width: 100%;
  max-width: 420px;
  background: var(--card);
  border-radius: 28px 28px 0 0;
  max-height: 78vh;
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom, 0);
  box-shadow: 0 -10px 40px rgba(160, 90, 30, 0.25);
  position: relative;
  overflow: hidden;
}

.sheet-handle {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--rule);
  margin: 10px auto 2px;
  flex-shrink: 0;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px 10px;
  flex-shrink: 0;
}

.sheet-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--ink-strong);
  letter-spacing: -0.02em;
}

.sheet-title .food-icon {
  display: inline-flex;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}
.sheet-title .food-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.sheet-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--card-soft);
  color: var(--ink-soft);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.sheet-close:active {
  background: var(--card-warm);
}

/* 概览条 */
.meta-bar {
  display: flex;
  gap: 8px;
  padding: 0 20px 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.meta-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: var(--r-pill);
  background: var(--card-soft);
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 600;
  gap: 6px;
}
.meta-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: linear-gradient(180deg, var(--accent-btn-start), var(--accent-btn-end));
  flex-shrink: 0;
}

/* 滚动区 */
.sheet-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 8px;
  -webkit-overflow-scrolling: touch;
}
.sheet-scroll::-webkit-scrollbar {
  width: 4px;
}
.sheet-scroll::-webkit-scrollbar-thumb {
  background: var(--rule);
  border-radius: 2px;
}

/* 区块 */
.recipe-section {
  padding-top: 14px;
}
.recipe-section + .recipe-section {
  border-top: 1px dashed var(--rule-dashed);
  margin-top: 14px;
  padding-top: 14px;
}

.section-title {
  position: relative;
  font-size: 1rem;
  font-weight: 800;
  color: var(--ink-strong);
  margin: 0 0 10px;
  padding-left: 10px;
  letter-spacing: -0.01em;
}
.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 3px;
  bottom: 3px;
  width: 3px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--accent-btn-start), var(--accent-btn-end));
}

/* 食材 */
.ingredient-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 14px;
}
.ingredient-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.92rem;
  color: var(--ink);
  line-height: 1.5;
  font-weight: 500;
}
.ing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}

/* 步骤时间轴 */
.step-list {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}
.step-list li {
  display: flex;
  gap: 12px;
  padding-bottom: 14px;
  position: relative;
}
.step-list li:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 13px;
  top: 28px;
  bottom: 0;
  width: 1.5px;
  background: var(--rule);
}
.step-num {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(180deg, var(--accent-btn-start), var(--accent-btn-end));
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 800;
  position: relative;
  z-index: 1;
  box-shadow: 0 2px 8px rgba(196, 98, 45, 0.3);
}
.step-list p {
  margin: 4px 0 0;
  font-size: 0.92rem;
  color: var(--ink);
  line-height: 1.6;
  font-weight: 500;
}

/* 小贴士 */
.tip-block {
  background: var(--card-warm);
  border-radius: 14px;
  padding: 12px 14px;
  border-left: 3px solid var(--accent);
}
.tip-block p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--ink);
  line-height: 1.55;
  font-weight: 500;
}

.sheet-foot-gap {
  height: 20px;
}

/* ===== 动画 ===== */
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.28s ease;
}
.sheet-enter-active .sheet-body,
.sheet-leave-active .sheet-body {
  transition: transform 0.3s cubic-bezier(0.33, 1, 0.68, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet-body,
.sheet-leave-to .sheet-body {
  transform: translateY(100%);
}
</style>
