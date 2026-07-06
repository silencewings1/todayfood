<template>
  <div class="app-logo" :class="size">
    <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="logoBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#ebb06a"/>
          <stop offset="50%" stop-color="#e08840"/>
          <stop offset="100%" stop-color="#c4622d"/>
        </linearGradient>
        <linearGradient id="logoBowl" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#fffef8"/>
          <stop offset="100%" stop-color="#f5e6d0"/>
        </linearGradient>
      </defs>
      <path d="M15 0 H49 Q64 0 64 15 V49 Q64 64 49 64 H15 Q0 64 0 49 V15 Q0 0 15 0 Z" fill="url(#logoBg)"/>
      <circle cx="32" cy="30" r="28" fill="rgba(255,255,255,0.06)"/>
      <path d="M14 30 Q14 46 32 46 Q50 46 50 30 Z" fill="url(#logoBowl)" opacity="0.95"/>
      <ellipse cx="32" cy="30" rx="20" ry="6" fill="#fffef8"/>
      <ellipse cx="32" cy="30" rx="16" ry="4.2" fill="#f0dcc4"/>
      <ellipse cx="32" cy="28" rx="12" ry="3.5" fill="#faf0e0"/>
      <rect x="20" y="10" width="3" height="30" rx="1.5" fill="#fff" opacity="0.9" transform="rotate(-12 21.5 25)"/>
      <rect x="41" y="10" width="3" height="30" rx="1.5" fill="#fff" opacity="0.9" transform="rotate(12 42.5 25)"/>
      <path d="M24 22 C22 17, 26 15, 24 10" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity="0.75"/>
      <path d="M32 20 C30 15, 34 13, 32 8" fill="none" stroke="#fff" stroke-width="2.8" stroke-linecap="round" opacity="0.85"/>
      <path d="M40 22 C38 17, 42 15, 40 10" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity="0.75"/>
      <rect x="28" y="46" width="8" height="3" rx="1.5" fill="#fff" opacity="0.6"/>
      <ellipse cx="32" cy="50" rx="10" ry="2" fill="#fff" opacity="0.4"/>
    </svg>
  </div>
</template>

<script setup>
defineProps({
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md', 'lg'].includes(v)
  }
})
</script>

<style scoped>
.app-logo {
  display: inline-flex;
  flex-shrink: 0;
  border-radius: 22%;
  overflow: hidden;
}

.app-logo svg {
  display: block;
  width: 100%;
  height: 100%;
}

.app-logo.sm {
  width: 34px;
  height: 34px;
}

.app-logo.md {
  width: 56px;
  height: 56px;
}

.app-logo.lg {
  width: 96px;
  height: 96px;
}
</style>
