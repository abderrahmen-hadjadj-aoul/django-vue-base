// Lightweight auth store built on Vue reactivity (no Pinia needed) so the
// template stays dependency-light. Import `useAuth()` anywhere to read the
// current user and call the auth actions.
//
// Authentication is session-cookie based: the backend sets an HttpOnly session
// cookie on login and a readable CSRF cookie; the API client (src/api/index.ts)
// attaches credentials and the CSRF header automatically.
import { computed, readonly, ref } from 'vue'

import {
  authCsrfRetrieve,
  authLoginCreate,
  authLogoutCreate,
  authMeRetrieve,
  authPasswordChangeCreate,
  authPasswordResetConfirmCreate,
  authPasswordResetCreate,
  authRegisterCreate,
  type User,
} from '@/api'

// Module-level singleton state — shared across every component that calls useAuth().
const user = ref<User | null>(null)
const ready = ref(false)

const isAuthenticated = computed(() => user.value !== null)

// Extract a human-readable message from a DRF error body.
function messageFrom(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const body = error as Record<string, unknown>
    if (typeof body.detail === 'string') return body.detail
    // Field errors look like { field: ["msg", ...] } — surface the first one.
    for (const value of Object.values(body)) {
      if (Array.isArray(value) && typeof value[0] === 'string') return value[0]
      if (typeof value === 'string') return value
    }
  }
  return fallback
}

// Fetch the CSRF cookie and the current user. Call once on app start.
async function bootstrap(): Promise<void> {
  await authCsrfRetrieve()
  const { data } = await authMeRetrieve()
  user.value = data ?? null
  ready.value = true
}

async function login(email: string, password: string): Promise<void> {
  const { data, error } = await authLoginCreate({ body: { email, password } })
  if (error || !data) throw new Error(messageFrom(error, 'Login failed.'))
  user.value = data
}

async function register(body: {
  email: string
  password: string
  first_name?: string
  last_name?: string
}): Promise<void> {
  const { data, error } = await authRegisterCreate({ body })
  if (error || !data) throw new Error(messageFrom(error, 'Registration failed.'))
  user.value = data
}

async function logout(): Promise<void> {
  await authLogoutCreate()
  user.value = null
}

async function changePassword(oldPassword: string, newPassword: string): Promise<string> {
  const { data, error } = await authPasswordChangeCreate({
    body: { old_password: oldPassword, new_password: newPassword },
  })
  if (error || !data) throw new Error(messageFrom(error, 'Could not change password.'))
  return data.detail
}

async function requestPasswordReset(email: string): Promise<string> {
  const { data, error } = await authPasswordResetCreate({ body: { email } })
  if (error || !data) throw new Error(messageFrom(error, 'Could not send reset email.'))
  return data.detail
}

async function confirmPasswordReset(
  uid: string,
  token: string,
  newPassword: string,
): Promise<string> {
  const { data, error } = await authPasswordResetConfirmCreate({
    body: { uid, token, new_password: newPassword },
  })
  if (error || !data) throw new Error(messageFrom(error, 'Could not reset password.'))
  return data.detail
}

export function useAuth() {
  return {
    user: readonly(user),
    ready: readonly(ready),
    isAuthenticated,
    bootstrap,
    login,
    register,
    logout,
    changePassword,
    requestPasswordReset,
    confirmPasswordReset,
  }
}
