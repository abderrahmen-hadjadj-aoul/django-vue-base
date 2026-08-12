<script setup lang="ts">
import { ref } from 'vue'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  <Card class="mx-auto max-w-sm">
    <CardHeader>
      <CardTitle class="text-2xl">Account</CardTitle>
    </CardHeader>
    <CardContent>
      <p class="text-sm text-muted-foreground">
        Signed in as
        <strong class="text-foreground" data-testid="account-email">{{ user?.email }}</strong>
      </p>

      <h3 class="mt-6 mb-3 text-lg font-semibold">Change password</h3>
      <form class="flex flex-col gap-4" data-testid="password-form" @submit.prevent="submit">
        <div class="grid gap-2">
          <Label for="old-password">Current password</Label>
          <Input
            id="old-password"
            v-model="oldPassword"
            type="password"
            autocomplete="current-password"
            required
            data-testid="account-old-password"
          />
        </div>
        <div class="grid gap-2">
          <Label for="new-password">New password</Label>
          <Input
            id="new-password"
            v-model="newPassword"
            type="password"
            autocomplete="new-password"
            required
            data-testid="account-new-password"
          />
        </div>
        <Button type="submit" :disabled="busy" data-testid="account-submit">
          {{ busy ? 'Saving…' : 'Update password' }}
        </Button>
      </form>
      <p v-if="message" class="mt-3 text-sm text-primary" data-testid="account-message">
        {{ message }}
      </p>
      <p v-if="error" class="mt-3 text-sm text-destructive" data-testid="account-error">
        {{ error }}
      </p>
    </CardContent>
  </Card>
</template>
