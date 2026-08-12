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
  <section class="auth">
    <h2>Account</h2>
    <p class="status">
      Signed in as <strong>{{ user?.email }}</strong>
    </p>

    <h3>Change password</h3>
    <form @submit.prevent="submit">
      <input
        v-model="oldPassword"
        type="password"
        placeholder="Current password"
        autocomplete="current-password"
        required
      />
      <input
        v-model="newPassword"
        type="password"
        placeholder="New password"
        autocomplete="new-password"
        required
      />
      <button type="submit" :disabled="busy">{{ busy ? 'Saving…' : 'Update password' }}</button>
    </form>
    <p v-if="message" class="success">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>
