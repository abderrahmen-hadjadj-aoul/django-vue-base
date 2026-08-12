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
  <section class="mx-auto max-w-sm">
    <h2 class="mb-4 text-2xl font-bold">Create an account</h2>
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
        autocomplete="new-password"
        required
      />
      <button type="submit" class="btn" :disabled="busy">
        {{ busy ? 'Creating…' : 'Sign up' }}
      </button>
    </form>
    <p v-if="error" class="mt-3 text-red-700">{{ error }}</p>
    <p class="mt-4 text-sm text-slate-600">
      Already have an account?
      <RouterLink to="/login" class="text-brand-hover hover:underline">Log in</RouterLink>
    </p>
  </section>
</template>
