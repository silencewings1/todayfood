<template>
  <header class="app-header">
    <div class="top-brand">
      <AppLogo size="sm" />
      <h1 class="brand-title">{{ title }}</h1>
    </div>
    <div class="top-right">
      <slot name="right">
        <span v-if="dateText" class="date-text">{{ dateText }}</span>
      </slot>
    </div>
  </header>
</template>

<script setup>
import AppLogo from '@/components/AppLogo.vue'

defineProps({
  title: { type: String, default: '今日宜吃 / today food' },
  dateText: { type: String, default: '' }
})
</script>

<style scoped>
/* ===== 顶部固定栏（sticky，适配灵动岛） ===== */
.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: calc(env(safe-area-inset-top, 0) + 10px) var(--pad-page) 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, #f7ead6 0%, #f7ead6 78%, rgba(247, 234, 214, 0) 100%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.top-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--ink-strong);
  letter-spacing: 0;
  margin: 0;
  white-space: nowrap;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-text {
  font-size: 0.78rem;
  color: var(--ink-soft);
  font-weight: 500;
  white-space: nowrap;
  letter-spacing: 0.02em;
}
</style>
