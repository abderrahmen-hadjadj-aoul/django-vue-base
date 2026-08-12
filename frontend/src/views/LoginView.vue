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
  <section class="auth">
    <h2>Log in</h2>
    <form @submit.prevent="submit">
      <input v-model="email" type="email" placeholder="Email" autocomplete="email" required />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        autocomplete="current-password"
        required
      />
      <button type="submit" :disabled="busy">{{ busy ? 'Logging in…' : 'Log in' }}</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="links">
      <RouterLink to="/register">Create an account</RouterLink>
      ·
      <RouterLink to="/forgot-password">Forgot password?</RouterLink>
    </p>
  </section>
</template>
