<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuth } from '@/stores/auth'

const { user, isAuthenticated, logout } = useAuth()
const router = useRouter()

async function onLogout() {
  await logout()
  await router.replace('/login')
}
</script>

<template>
  <header
    class="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-3"
  >
    <RouterLink to="/" class="font-bold text-slate-900">Django + Vue Base</RouterLink>
    <nav v-if="isAuthenticated" class="flex items-center gap-4">
      <RouterLink to="/" class="text-brand-hover hover:underline">Home</RouterLink>
      <RouterLink to="/account" class="text-brand-hover hover:underline">Account</RouterLink>
      <span class="text-sm text-slate-500">{{ user?.email }}</span>
      <button
        type="button"
        class="cursor-pointer font-semibold text-red-700 hover:underline"
        @click="onLogout"
      >
        Log out
      </button>
    </nav>
  </header>

  <main class="mx-auto max-w-2xl px-6 py-12">
    <RouterView />
  </main>
</template>
