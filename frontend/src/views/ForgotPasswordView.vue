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
  <section class="auth">
    <h2>Reset your password</h2>
    <p class="status">Enter your email and we'll send you a reset link.</p>
    <form @submit.prevent="submit">
      <input v-model="email" type="email" placeholder="Email" autocomplete="email" required />
      <button type="submit" :disabled="busy">{{ busy ? 'Sending…' : 'Send link' }}</button>
    </form>
    <p v-if="message" class="success">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="links">
      <RouterLink to="/login">Back to log in</RouterLink>
    </p>
  </section>
</template>
