<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  <Card class="mx-auto max-w-sm">
    <CardHeader>
      <CardTitle class="text-2xl">Create an account</CardTitle>
    </CardHeader>
    <CardContent>
      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <div class="grid gap-2">
          <Label for="email">Email</Label>
          <Input id="email" v-model="email" type="email" autocomplete="email" required />
        </div>
        <div class="grid gap-2">
          <Label for="password">Password</Label>
          <Input
            id="password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
          />
        </div>
        <Button type="submit" :disabled="busy">{{ busy ? 'Creating…' : 'Sign up' }}</Button>
      </form>
      <p v-if="error" class="mt-3 text-sm text-destructive">{{ error }}</p>
      <p class="mt-4 text-sm text-muted-foreground">
        Already have an account?
        <RouterLink to="/login" class="text-foreground underline-offset-4 hover:underline">
          Log in
        </RouterLink>
      </p>
    </CardContent>
  </Card>
</template>
