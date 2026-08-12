<script setup lang="ts">
import { useRouter } from 'vue-router'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/stores/auth'

const { user, isAuthenticated, logout } = useAuth()
const router = useRouter()

async function onLogout() {
  await logout()
  await router.replace('/login')
}
</script>

<template>
  <header class="flex items-center justify-between gap-4 border-b bg-card px-6 py-3">
    <RouterLink to="/" class="font-bold text-foreground">Django + Vue Base</RouterLink>
    <nav v-if="isAuthenticated" class="flex items-center gap-4">
      <RouterLink to="/" class="text-sm text-muted-foreground hover:text-foreground">Home</RouterLink>
      <RouterLink to="/account" class="text-sm text-muted-foreground hover:text-foreground">
        Account
      </RouterLink>
      <span class="text-sm text-muted-foreground">{{ user?.email }}</span>
      <Button variant="ghost" size="sm" class="text-destructive" @click="onLogout">Log out</Button>
    </nav>
  </header>

  <main class="mx-auto max-w-2xl px-6 py-12">
    <RouterView />
  </main>
</template>
