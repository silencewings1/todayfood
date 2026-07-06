<template>
  <div class="about-view">
    <!-- 顶部固定栏 -->
    <AppHeader title="关于" />

    <!-- 居中 logo + 标题 -->
    <section class="brand-center page">
      <AppLogo size="lg" />
      <h1 class="about-title">今日宜吃</h1>
      <p class="about-sub accent">AI + 黄历 · 生活娱乐赛道</p>
      <p class="about-sub">用黄历决定今天吃什么</p>
    </section>

    <div class="page"><div class="dashed-divider"></div></div>

    <!-- 创意介绍 -->
    <section class="page section-block">
      <h2 class="section-title">创意介绍</h2>

      <div class="about-card">
        <span class="badge-orange">痛点</span>
        <h3 class="card-h">选择困难症日常发作</h3>
        <p class="card-p">外卖看半天、朋友问一圈，最后还是"都行"。每天最难的小问题，从来不是人生方向。</p>
      </div>

      <div class="about-card">
        <span class="badge-orange">灵感</span>
        <h3 class="card-h">把黄历的"宜忌"装进菜单</h3>
        <p class="card-p">黄历宜忌自带仪式感和娱乐性，配上 AI 推荐，吃饭选择变得轻松又好玩。</p>
      </div>
    </section>

    <!-- 怎么玩 -->
    <section class="page section-block">
      <h2 class="section-title">怎么玩</h2>

      <div class="step-card" v-for="(step, i) in steps" :key="i">
        <span class="badge-circle">{{ i + 1 }}</span>
        <div class="step-content">
          <h3 class="card-h">{{ step.title }}</h3>
          <p class="card-p">{{ step.desc }}</p>
        </div>
      </div>
    </section>

    <p class="disclaimer">娱乐参考，不代表真实预测 · 认真吃饭，开心最重要</p>
  </div>
</template>

<script setup>
import AppLogo from '@/components/AppLogo.vue'
import AppHeader from '@/components/AppHeader.vue'
const steps = [
  { title: '看今日食历', desc: '打开即见黄历宜忌，今日食运一目了然。' },
  { title: '选一选状态', desc: '告诉食神你的心情和口味偏好，让推荐更懂你。' },
  { title: '抽一支饭签', desc: '食神为你定一道菜，附一句开运理由。' },
  { title: '复制分享给饭搭子', desc: '把今日饭签发给朋友，一起吃才有仪式感。' }
]
</script>

<style scoped>
.about-view {
  min-height: 100%;
  padding-bottom: 12px;
}

/* 居中 logo */
.brand-center {
  padding-top: 12px;
  padding-bottom: 8px;
  text-align: center;
}

.about-title {
  font-size: 1.7rem;
  font-weight: 900;
  color: var(--ink-strong);
  letter-spacing: 0.04em;
  margin: 0 0 6px;
}

.about-sub {
  font-size: 0.82rem;
  color: var(--ink-soft);
  margin: 3px 0;
  letter-spacing: 0.02em;
}

.about-sub.accent {
  color: var(--accent);
  font-weight: 600;
}

/* 区块 */
.section-block {
  padding-top: 4px;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 900;
  color: var(--ink-strong);
  letter-spacing: -0.02em;
  margin: 0 0 8px;
}

.about-card {
  background: var(--card);
  border-radius: var(--r-card);
  padding: 14px 16px;
  margin-bottom: 8px;
}

.card-h {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--ink-strong);
  margin: 6px 0 4px;
  letter-spacing: -0.01em;
}

.card-p {
  font-size: 0.82rem;
  color: var(--ink-soft);
  line-height: 1.5;
  margin: 0;
}

.step-card {
  background: var(--card);
  border-radius: var(--r-card);
  padding: 14px 16px;
  margin-bottom: 8px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-content .card-h {
  margin-top: 2px;
}

.disclaimer {
  padding: 6px 0 2px;
  font-size: 0.72rem;
}
</style>
