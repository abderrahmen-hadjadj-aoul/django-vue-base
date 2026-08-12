<script setup lang="ts">
import { ref } from 'vue'

import { useAuth } from '@/stores/auth'

const { requestPasswordReset } = useAuth()

const email = ref('')
const message = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  message.value = ''
  busy.value = true
  try {
    message.value = await requestPasswordReset(email.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Could not send reset email.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-sm">
    <h2 class="mb-4 text-2xl font-bold">Reset your password</h2>
    <p class="text-slate-500">Enter your email and we'll send you a reset link.</p>
    <form class="mt-4 flex flex-col gap-3" @submit.prevent="submit">
      <input
        v-model="email"
        type="email"
        class="input"
        placeholder="Email"
        autocomplete="email"
        required
      />
      <button type="submit" class="btn" :disabled="busy">
        {{ busy ? 'Sending…' : 'Send link' }}
      </button>
    </form>
    <p v-if="message" class="mt-3 text-green-700">{{ message }}</p>
    <p v-if="error" class="mt-3 text-red-700">{{ error }}</p>
    <p class="mt-4 text-sm text-slate-600">
      <RouterLink to="/login" class="text-brand-hover hover:underline">Back to log in</RouterLink>
    </p>
  </section>
</template>
