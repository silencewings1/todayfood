import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/index'
  },
  {
    path: '/index',
    name: 'food',
    component: () => import('@/views/Home.vue'),
    meta: { tab: 'food', title: '今日宜吃 / today food' }
  },
  {
    path: '/pick',
    name: 'pick',
    component: () => import('@/views/Detail.vue'),
    meta: { tab: 'pick', title: '选一选' }
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('@/views/Mine.vue'),
    meta: { tab: 'about', title: '关于今日宜吃 / today food' }
  }
]

// 嵌入 snowflow 主站时，路由 base 跟随 vite 的 base 配置
// 开发环境 import.meta.env.BASE_URL 为 '/'，生产为 '/projects/todayfood/'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  }
})

export default router
