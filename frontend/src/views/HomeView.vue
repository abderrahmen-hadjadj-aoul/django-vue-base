<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { healthRetrieve, itemsCreate, itemsList, type Item } from '@/api'

const health = ref('checking…')
const items = ref<Item[]>([])
const name = ref('')
const description = ref('')
const error = ref('')

async function loadItems() {
  const { data } = await itemsList()
  // The list endpoint is paginated: rows live under `results`.
  items.value = data?.results ?? []
}

async function addItem() {
  if (!name.value.trim()) return
  error.value = ''
  const { error: err } = await itemsCreate({
    body: { name: name.value, description: description.value },
  })
  if (err) {
    error.value = 'Could not create item'
    return
  }
  name.value = ''
  description.value = ''
  await loadItems()
}

onMounted(async () => {
  const { data, error: err } = await healthRetrieve()
  if (err || !data) {
    health.value = 'unreachable'
    error.value = 'Backend is unreachable'
    return
  }
  health.value = data.status
  await loadItems()
})
</script>

<template>
  <section>
    <p class="text-sm text-muted-foreground">
      Backend health:
      <span
        class="ml-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
        :class="
          health === 'ok'
            ? 'bg-primary/10 text-primary'
            : 'bg-destructive/10 text-destructive'
        "
        data-testid="health-status"
        >{{ health }}</span
      >
    </p>

    <h2 class="mt-6 mb-1 text-xl font-bold">Items</h2>
    <form class="my-4 flex flex-wrap gap-2" data-testid="item-form" @submit.prevent="addItem">
      <Input v-model="name" class="flex-1" placeholder="Name" required data-testid="item-name" />
      <Input
        v-model="description"
        class="flex-1"
        placeholder="Description (optional)"
        data-testid="item-description"
      />
      <Button type="submit" data-testid="item-add">Add</Button>
    </form>
    <p v-if="error" class="text-sm text-destructive" data-testid="home-error">{{ error }}</p>
    <ul class="mt-2" data-testid="item-list">
      <li v-for="item in items" :key="item.id" class="border-b py-2" data-testid="item">
        <strong>{{ item.name }}</strong>
        <span v-if="item.description" class="text-muted-foreground"> — {{ item.description }}</span>
      </li>
      <li v-if="items.length === 0" class="py-2 text-muted-foreground" data-testid="item-empty">
        No items yet.
      </li>
    </ul>
  </section>
</template>
