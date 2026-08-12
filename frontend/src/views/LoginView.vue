<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/stores/auth'

const { login } = useAuth()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await login(email.value, password.value)
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    await router.replace(next)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Login failed.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Card class="mx-auto max-w-sm">
    <CardHeader>
      <CardTitle class="text-2xl">Log in</CardTitle>
    </CardHeader>
    <CardContent>
      <form class="flex flex-col gap-4" data-testid="login-form" @submit.prevent="submit">
        <div class="grid gap-2">
          <Label for="email">Email</Label>
          <Input
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            required
            data-testid="login-email"
          />
        </div>
        <div class="grid gap-2">
          <Label for="password">Password</Label>
          <Input
            id="password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            data-testid="login-password"
          />
        </div>
        <Button type="submit" :disabled="busy" data-testid="login-submit">
          {{ busy ? 'Logging in…' : 'Log in' }}
        </Button>
      </form>
      <p v-if="error" class="mt-3 text-sm text-destructive" data-testid="login-error">
        {{ error }}
      </p>
      <p class="mt-4 text-sm text-muted-foreground">
        <RouterLink
          to="/register"
          class="text-foreground underline-offset-4 hover:underline"
          data-testid="login-register-link"
        >
          Create an account
        </RouterLink>
        ·
        <RouterLink
          to="/forgot-password"
          class="text-foreground underline-offset-4 hover:underline"
          data-testid="login-forgot-link"
        >
          Forgot password?
        </RouterLink>
      </p>
    </CardContent>
  </Card>
</template>
