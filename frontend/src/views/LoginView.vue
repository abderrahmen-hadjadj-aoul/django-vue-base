<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuth } from '@/stores/auth'

const { login } = useAuth()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await login(email.value, password.value)
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    await router.replace(next)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Login failed.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-sm">
    <h2 class="mb-4 text-2xl font-bold">Log in</h2>
    <form class="flex flex-col gap-3" @submit.prevent="submit">
      <input
        v-model="email"
        type="email"
        class="input"
        placeholder="Email"
        autocomplete="email"
        required
      />
      <input
        v-model="password"
        type="password"
        class="input"
        placeholder="Password"
        autocomplete="current-password"
        required
      />
      <button type="submit" class="btn" :disabled="busy">
        {{ busy ? 'Logging in…' : 'Log in' }}
      </button>
    </form>
    <p v-if="error" class="mt-3 text-red-700">{{ error }}</p>
    <p class="mt-4 text-sm text-slate-600">
      <RouterLink to="/register" class="text-brand-hover hover:underline">
        Create an account
      </RouterLink>
      ·
      <RouterLink to="/forgot-password" class="text-brand-hover hover:underline">
        Forgot password?
      </RouterLink>
    </p>
  </section>
</template>
