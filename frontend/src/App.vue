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
    <RouterLink to="/" class="font-bold text-foreground" data-testid="brand">Django + Vue Base</RouterLink>
    <nav v-if="isAuthenticated" class="flex items-center gap-4" data-testid="main-nav">
      <RouterLink
        to="/"
        class="text-sm text-muted-foreground hover:text-foreground"
        data-testid="nav-home"
        >Home</RouterLink
      >
      <RouterLink
        to="/account"
        class="text-sm text-muted-foreground hover:text-foreground"
        data-testid="nav-account"
      >
        Account
      </RouterLink>
      <span class="text-sm text-muted-foreground" data-testid="nav-user-email">{{
        user?.email
      }}</span>
      <Button
        variant="ghost"
        size="sm"
        class="text-destructive"
        data-testid="logout-button"
        @click="onLogout"
        >Log out</Button
      >
    </nav>
  </header>

  <main class="mx-auto max-w-2xl px-6 py-12">
    <RouterView />
  </main>
</template>
