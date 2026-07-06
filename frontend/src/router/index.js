import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'food',
    component: () => import('@/views/Home.vue'),
    meta: { tab: 'food', title: '今日宜吃' }
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
    meta: { tab: 'about', title: '关于今日宜吃' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  }
})

export default router
