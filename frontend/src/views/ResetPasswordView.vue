<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { useAuth } from '@/stores/auth'

const { confirmPasswordReset } = useAuth()
const route = useRoute()

// The uid/token come from the link in the reset email
// (/reset-password?uid=...&token=...).
const uid = computed(() => (typeof route.query.uid === 'string' ? route.query.uid : ''))
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))

const password = ref('')
const message = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  message.value = ''
  busy.value = true
  try {
    message.value = await confirmPasswordReset(uid.value, token.value, password.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Could not reset password.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-sm">
    <h2 class="mb-4 text-2xl font-bold">Choose a new password</h2>
    <p v-if="!uid || !token" class="text-red-700">
      This reset link is missing its token. Request a new one from
      <RouterLink to="/forgot-password" class="text-brand-hover hover:underline">
        Forgot password </RouterLink
      >.
    </p>
    <form v-else class="flex flex-col gap-3" @submit.prevent="submit">
      <input
        v-model="password"
        type="password"
        class="input"
        placeholder="New password"
        autocomplete="new-password"
        required
      />
      <button type="submit" class="btn" :disabled="busy">
        {{ busy ? 'Saving…' : 'Set password' }}
      </button>
    </form>
    <p v-if="message" class="mt-3 text-green-700">
      {{ message }}
      <RouterLink to="/login" class="text-brand-hover hover:underline">Log in</RouterLink>
    </p>
    <p v-if="error" class="mt-3 text-red-700">{{ error }}</p>
  </section>
</template>
