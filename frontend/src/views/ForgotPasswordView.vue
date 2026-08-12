<script setup lang="ts">
import { ref } from 'vue'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  <Card class="mx-auto max-w-sm">
    <CardHeader>
      <CardTitle class="text-2xl">Reset your password</CardTitle>
      <CardDescription>Enter your email and we'll send you a reset link.</CardDescription>
    </CardHeader>
    <CardContent>
      <form class="flex flex-col gap-4" data-testid="forgot-form" @submit.prevent="submit">
        <div class="grid gap-2">
          <Label for="email">Email</Label>
          <Input
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            required
            data-testid="forgot-email"
          />
        </div>
        <Button type="submit" :disabled="busy" data-testid="forgot-submit">
          {{ busy ? 'Sending…' : 'Send link' }}
        </Button>
      </form>
      <p v-if="message" class="mt-3 text-sm text-primary" data-testid="forgot-message">
        {{ message }}
      </p>
      <p v-if="error" class="mt-3 text-sm text-destructive" data-testid="forgot-error">
        {{ error }}
      </p>
      <p class="mt-4 text-sm text-muted-foreground">
        <RouterLink
          to="/login"
          class="text-foreground underline-offset-4 hover:underline"
          data-testid="forgot-login-link"
        >
          Back to log in
        </RouterLink>
      </p>
    </CardContent>
  </Card>
</template>
