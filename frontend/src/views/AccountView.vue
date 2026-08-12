<script setup lang="ts">
import { ref } from 'vue'

import { useAuth } from '@/stores/auth'

const { user, changePassword } = useAuth()

const oldPassword = ref('')
const newPassword = ref('')
const message = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  message.value = ''
  busy.value = true
  try {
    message.value = await changePassword(oldPassword.value, newPassword.value)
    oldPassword.value = ''
    newPassword.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Could not change password.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-sm">
    <h2 class="mb-4 text-2xl font-bold">Account</h2>
    <p class="text-slate-500">
      Signed in as <strong class="text-slate-900">{{ user?.email }}</strong>
    </p>

    <h3 class="mt-6 mb-3 text-lg font-semibold">Change password</h3>
    <form class="flex flex-col gap-3" @submit.prevent="submit">
      <input
        v-model="oldPassword"
        type="password"
        class="input"
        placeholder="Current password"
        autocomplete="current-password"
        required
      />
      <input
        v-model="newPassword"
        type="password"
        class="input"
        placeholder="New password"
        autocomplete="new-password"
        required
      />
      <button type="submit" class="btn" :disabled="busy">
        {{ busy ? 'Saving…' : 'Update password' }}
      </button>
    </form>
    <p v-if="message" class="mt-3 text-green-700">{{ message }}</p>
    <p v-if="error" class="mt-3 text-red-700">{{ error }}</p>
  </section>
</template>
