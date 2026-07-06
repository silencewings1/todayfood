<template>
  <div class="phone-shell">
    <div class="phone-shell__inner">
      <main class="app-main">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>
      <AppTabBar />
    </div>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import AppTabBar from '@/components/AppTabBar.vue'
</script>

<style>
.phone-shell {
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  position: relative;
}

@media (min-width: 768px) {
  .phone-shell {
    min-height: 100vh;
    min-height: 100dvh;
    padding: 24px 0;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    background:
      radial-gradient(circle at 20% 20%, rgba(232, 154, 92, 0.18), transparent 40%),
      radial-gradient(circle at 80% 80%, rgba(196, 98, 45, 0.12), transparent 40%),
      #f0dec2;
  }

  .phone-shell__inner {
    width: 420px;
    height: calc(100vh - 48px);
    height: calc(100dvh - 48px);
    background: var(--bg);
    border-radius: 32px;
    overflow: hidden;
    box-shadow:
      0 30px 80px -20px rgba(140, 80, 40, 0.32),
      0 10px 30px -10px rgba(140, 80, 40, 0.18),
      0 0 0 1px rgba(196, 98, 45, 0.08);
    position: relative;
    display: flex;
    flex-direction: column;
  }
}

@media (max-width: 767px) {
  .phone-shell__inner {
    width: 100%;
    min-height: 100vh;
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    position: relative;
  }
}

.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 64px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
