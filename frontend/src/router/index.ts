import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useAuth } from '@/stores/auth'

// Routes with `meta.public` are reachable while logged out; everything else
// requires an authenticated session and redirects to /login otherwise.
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/account',
    name: 'account',
    component: () => import('@/views/AccountView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/views/ForgotPasswordView.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('@/views/ResetPasswordView.vue'),
    meta: { public: true },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const { ready, isAuthenticated, bootstrap } = useAuth()
  // Resolve the session once, before the first navigation.
  if (!ready.value) await bootstrap()

  if (!to.meta.public && !isAuthenticated.value) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  // Keep authenticated users out of the auth pages.
  if (to.meta.public && isAuthenticated.value) {
    return { name: 'home' }
  }
  return true
})
