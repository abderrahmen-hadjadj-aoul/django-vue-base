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
  <header class="topbar">
    <RouterLink to="/" class="brand">Django + Vue Base</RouterLink>
    <nav v-if="isAuthenticated">
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/account">Account</RouterLink>
      <span class="who">{{ user?.email }}</span>
      <button type="button" class="link-btn" @click="onLogout">Log out</button>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #e5e5ec;
  background: white;
}

.brand {
  font-weight: 700;
  color: #1a1a2e;
  text-decoration: none;
}

nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}

nav a {
  color: #369870;
  text-decoration: none;
}

.who {
  color: #555;
  font-size: 0.9rem;
}

.link-btn {
  background: none;
  border: none;
  color: #b42318;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.link-btn:hover {
  background: none;
  text-decoration: underline;
}
</style>
