<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  <Card class="mx-auto max-w-sm">
    <CardHeader>
      <CardTitle class="text-2xl">Choose a new password</CardTitle>
    </CardHeader>
    <CardContent>
      <p v-if="!uid || !token" class="text-sm text-destructive" data-testid="reset-missing-token">
        This reset link is missing its token. Request a new one from
        <RouterLink
          to="/forgot-password"
          class="text-foreground underline-offset-4 hover:underline"
        >
          Forgot password </RouterLink
        >.
      </p>
      <form v-else class="flex flex-col gap-4" data-testid="reset-form" @submit.prevent="submit">
        <div class="grid gap-2">
          <Label for="password">New password</Label>
          <Input
            id="password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            data-testid="reset-password"
          />
        </div>
        <Button type="submit" :disabled="busy" data-testid="reset-submit">
          {{ busy ? 'Saving…' : 'Set password' }}
        </Button>
      </form>
      <p v-if="message" class="mt-3 text-sm text-primary" data-testid="reset-message">
        {{ message }}
        <RouterLink to="/login" class="text-foreground underline-offset-4 hover:underline">
          Log in
        </RouterLink>
      </p>
      <p v-if="error" class="mt-3 text-sm text-destructive" data-testid="reset-error">
        {{ error }}
      </p>
    </CardContent>
  </Card>
</template>
