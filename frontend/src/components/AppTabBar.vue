<template>
  <nav class="tabbar safe-bottom">
    <RouterLink
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.to"
      class="tab-item"
      :class="{ active: active === tab.key }"
    >
      <span class="tab-icon" v-html="tab.icon"></span>
      <span class="tab-label">{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = computed(() => route.meta?.tab || 'food')

const tabs = [
  {
    key: 'food',
    label: '食历',
    to: '/',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="18" height="17" rx="3"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <path d="M9 14 Q12 17 15 14" fill="none"/>
      <circle cx="9" cy="14" r="0.6" fill="currentColor"/>
      <circle cx="15" cy="14" r="0.6" fill="currentColor"/>
    </svg>`
  },
  {
    key: 'pick',
    label: '择食',
    to: '/pick',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="10" r="7"/>
      <path d="M12 6 L12 10 L15 13"/>
      <path d="M9 19 L12 22 L15 19"/>
      <line x1="12" y1="15" x2="12" y2="22"/>
    </svg>`
  },
  {
    key: 'about',
    label: '关于',
    to: '/about',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="8" r="3.5"/>
      <path d="M5 20 Q5 14 12 14 Q19 14 19 20"/>
    </svg>`
  }
]
</script>

<style scoped>
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  height: 60px;
  padding-bottom: env(safe-area-inset-bottom, 0);
  background: var(--card);
  border-top: 1px solid var(--rule);
}

@media (min-width: 768px) {
  .tabbar {
    max-width: 420px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 1px solid var(--rule);
    border-right: 1px solid var(--rule);
    border-bottom-left-radius: 32px;
    border-bottom-right-radius: 32px;
    overflow: hidden;
  }
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  color: var(--ink-muted);
  text-decoration: none;
  -webkit-tap-highlight-color: transparent;
  transition: color 0.2s;
}

.tab-item:active {
  opacity: 0.7;
}

.tab-item.active {
  color: var(--accent);
}

.tab-icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.tab-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.tab-item.active .tab-icon {
  transform: scale(1.08);
}

.tab-label {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
</style>
