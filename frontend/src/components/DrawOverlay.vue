<template>
  <transition name="overlay-fade">
    <div v-if="visible" class="draw-inline">
      <!-- 背景光晕 -->
      <div class="glow" :class="{ burst: phase === 'burst' }"></div>

      <!-- 扩散圆环 -->
      <div class="rings" v-if="phase === 'burst'">
        <span class="ring ring-1"></span>
        <span class="ring ring-2"></span>
      </div>

      <!-- 飞散的小签条 -->
      <div class="sticks" v-if="phase === 'burst'">
        <span v-for="n in 6" :key="n" class="stick" :class="`stick-${n}`"></span>
      </div>

      <!-- 签筒 -->
      <div class="tube-wrap" :class="{ shake: phase === 'shake', pop: phase === 'burst' }">
        <div class="tube">
          <div class="tube-top"></div>
          <div class="tube-body">
            <div class="tube-char">签</div>
          </div>
          <div class="tube-sticks" :class="{ wiggle: phase === 'shake' }">
            <span v-for="n in 4" :key="n" class="mini-stick" :class="`ms-${n}`"></span>
          </div>
        </div>
      </div>

      <!-- 提示文字 -->
      <div class="draw-tip">
        <span v-if="phase === 'enter' || phase === 'shake'">摇签中…</span>
        <span v-else>签出！</span>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { DRAW_MIN_DURATION } from '@/config'

const props = defineProps({
  visible: { type: Boolean, default: false },
  /**
   * 关联的 API 请求 Promise（可选）。
   * 若提供：shake 阶段会一直持续到该 Promise 完成（resolve/reject 均算完成）；
   * 若不提供：仅按最短时长结束。
   */
  promise: { type: Promise, default: null }
})
const emit = defineEmits(['finished'])

const phase = ref('enter')

// enter / burst 阶段固定时长，shake 阶段动态延长
const ENTER_MS = 400
const BURST_MS = 700
// 从 run() 开始算，最早可进入 burst 的时间点（预留 burst 时长，保证总时长 >= DRAW_MIN_DURATION）
const MIN_TOTAL_BEFORE_BURST = Math.max(ENTER_MS, DRAW_MIN_DURATION - BURST_MS)

let timers = []
let startTime = 0
let apiDone = false

function clearAllTimers() {
  timers.forEach(t => clearTimeout(t))
  timers = []
}

/** 尝试从 shake 推进到 burst：需要「最短时长到达」且「API 返回」两个条件同时满足 */
function tryEnterBurst() {
  if (phase.value !== 'shake') return
  const elapsed = Date.now() - startTime
  if (elapsed >= MIN_TOTAL_BEFORE_BURST && apiDone) {
    enterBurst()
  } else if (apiDone) {
    // API 已返回，但最短时长未到 → 等待剩余时间
    const remaining = Math.max(0, MIN_TOTAL_BEFORE_BURST - elapsed)
    timers.push(setTimeout(() => {
      if (phase.value === 'shake') enterBurst()
    }, remaining))
  }
  // 若 API 未返回，等其 resolve/reject 回调里再次调用 tryEnterBurst
}

function enterBurst() {
  if (phase.value !== 'shake') return
  phase.value = 'burst'
  timers.push(setTimeout(() => {
    emit('finished')
  }, BURST_MS))
}

function run() {
  clearAllTimers()
  phase.value = 'enter'
  apiDone = false
  startTime = Date.now()

  // 监听 API Promise（resolve/reject 均视为完成）
  const p = props.promise
  if (p && typeof p.then === 'function') {
    p.then(() => { apiDone = true; tryEnterBurst() })
     .catch(() => { apiDone = true; tryEnterBurst() })
  } else {
    // 没有关联请求，直接视为完成
    apiDone = true
  }

  // enter → shake
  timers.push(setTimeout(() => {
    phase.value = 'shake'
    tryEnterBurst()
  }, ENTER_MS))
}

watch(() => props.visible, (v) => {
  if (v) run()
  else {
    clearAllTimers()
    phase.value = 'enter'
  }
})
</script>

<style scoped>
.draw-inline {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at center, rgba(247, 234, 214, 0.92) 0%, rgba(224, 196, 158, 0.96) 100%);
  overflow: hidden;
  border-radius: inherit;
}

/* 光晕 */
.glow {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 100px;
  height: 100px;
  margin: -50px 0 0 -50px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232, 154, 92, 0.5) 0%, rgba(232, 154, 92, 0) 70%);
  transition: all 0.4s;
}
.glow.burst {
  width: 280px;
  height: 280px;
  margin: -140px 0 0 -140px;
  background: radial-gradient(circle, rgba(255, 220, 140, 0.8) 0%, rgba(232, 154, 92, 0.3) 40%, rgba(232, 154, 92, 0) 75%);
}

/* 签筒 */
.tube-wrap {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  transform-origin: bottom center;
}
.tube-wrap.shake {
  animation: tubeShake 0.32s linear infinite;
}
.tube-wrap.pop {
  animation: tubePop 0.4s cubic-bezier(0.2, 0.8, 0.3, 1.2) forwards;
}

@keyframes tubeShake {
  0%   { transform: rotate(-10deg) translateX(-3px); }
  25%  { transform: rotate(7deg)  translateX(3px); }
  50%  { transform: rotate(-9deg) translateX(-3px); }
  75%  { transform: rotate(10deg) translateX(3px); }
  100% { transform: rotate(-5deg) translateX(-2px); }
}
@keyframes tubePop {
  0%   { transform: scale(1); opacity: 1; }
  40%  { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.3) translateY(-40px); opacity: 0; }
}

.tube {
  position: relative;
  width: 56px;
  height: 88px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.tube-top {
  width: 64px;
  height: 9px;
  background: linear-gradient(180deg, #d8823a, #a04a18);
  border-radius: 3px 3px 2px 2px;
  box-shadow: 0 1px 3px rgba(120, 60, 20, 0.25);
  z-index: 3;
}
.tube-body {
  width: 56px;
  flex: 1;
  background: linear-gradient(90deg, #a04a18 0%, #c4622d 30%, #e89a5c 60%, #c4622d 85%, #8a3c10 100%);
  border-radius: 0 0 6px 6px;
  box-shadow: inset -4px 0 8px rgba(0,0,0,0.2), inset 4px 0 8px rgba(255,220,160,0.2), 0 4px 12px rgba(140,70,20,0.3);
  display: grid;
  place-items: center;
  position: relative;
}
.tube-char {
  color: #fff2d8;
  font-size: 1.7rem;
  font-weight: 900;
  text-shadow: 0 1px 4px rgba(0,0,0,0.25);
}

.tube-sticks {
  position: absolute;
  top: -26px;
  left: 50%;
  transform: translateX(-50%);
  width: 44px;
  height: 26px;
  z-index: 2;
}
.mini-stick {
  position: absolute;
  bottom: 0;
  width: 3px;
  height: 24px;
  background: linear-gradient(180deg, #f3d89a, #c89754);
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
  transform-origin: bottom center;
}
.ms-1 { left: 6px;  height: 20px; transform: rotate(-8deg); --r: -8deg; }
.ms-2 { left: 16px; height: 25px; transform: rotate(-2deg); --r: -2deg; }
.ms-3 { left: 26px; height: 28px; transform: rotate(3deg);  --r: 3deg; }
.ms-4 { left: 36px; height: 22px; transform: rotate(8deg);  --r: 8deg; }

.tube-sticks.wiggle .mini-stick {
  animation: stickWiggle 0.26s linear infinite alternate;
}
@keyframes stickWiggle {
  from { transform: rotate(var(--r)) translateY(0); }
  to   { transform: rotate(calc(var(--r) + 5deg)) translateY(-3px); }
}

/* 扩散圆环 */
.rings {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 0;
  height: 0;
  z-index: 1;
}
.ring {
  position: absolute;
  left: 0;
  top: 0;
  border: 2px solid rgba(232, 154, 92, 0.7);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: ringExpand 0.6s ease-out forwards;
}
.ring-2 { animation-delay: 0.12s; border-color: rgba(255, 220, 140, 0.7); }
@keyframes ringExpand {
  0%   { width: 20px; height: 20px; opacity: 1; }
  100% { width: 240px; height: 240px; opacity: 0; margin-left: -120px; margin-top: -120px; }
}

/* 飞散的小签条 */
.sticks {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 0;
  height: 0;
  z-index: 2;
}
.stick {
  position: absolute;
  width: 4px;
  height: 30px;
  background: linear-gradient(180deg, #f3d89a, #c89754);
  border-radius: 2px;
  left: -2px;
  top: -15px;
  transform-origin: center center;
  animation: stickFly 0.55s cubic-bezier(0.2, 0.6, 0.3, 1) forwards;
}
.stick-1 { --tx: -90px;  --ty: -100px; --rot: -320deg; }
.stick-2 { --tx: -40px;  --ty: -120px; --rot: 260deg; }
.stick-3 { --tx: 50px;   --ty: -115px; --rot: -240deg; }
.stick-4 { --tx: 100px;  --ty: -85px;  --rot: 300deg; }
.stick-5 { --tx: 95px;   --ty: 40px;   --rot: -180deg; }
.stick-6 { --tx: -90px;  --ty: 50px;   --rot: 200deg; }
@keyframes stickFly {
  0%   { transform: translate(0,0) rotate(0) scale(1); opacity: 1; }
  100% { transform: translate(var(--tx), var(--ty)) rotate(var(--rot)) scale(0.6); opacity: 0; }
}

/* 提示文字 */
.draw-tip {
  position: absolute;
  bottom: 14px;
  left: 0;
  right: 0;
  text-align: center;
  color: var(--accent-deep, #7a3c18);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  z-index: 3;
}

.overlay-fade-enter-active {
  transition: opacity 0.2s;
}
.overlay-fade-leave-active {
  transition: opacity 0.25s;
}
.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}
</style>
