<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuth } from '@/stores/auth'

const { register } = useAuth()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await register({ email: email.value, password: password.value })
    await router.replace('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Registration failed.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="auth">
    <h2>Create an account</h2>
    <form @submit.prevent="submit">
      <input v-model="email" type="email" placeholder="Email" autocomplete="email" required />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        autocomplete="new-password"
        required
      />
      <button type="submit" :disabled="busy">{{ busy ? 'Creating…' : 'Sign up' }}</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="links">
      Already have an account?
      <RouterLink to="/login">Log in</RouterLink>
    </p>
  </section>
</template>
