<script setup lang="ts">
import { onMounted, ref } from 'vue'

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
    <p class="text-slate-500">
      Backend health:
      <span
        class="ml-1 rounded-full px-2 py-0.5 text-sm font-semibold"
        :class="health === 'ok' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
        >{{ health }}</span
      >
    </p>

    <h2 class="mt-6 mb-1 text-xl font-bold">Items</h2>
    <form class="my-4 flex flex-wrap gap-2" @submit.prevent="addItem">
      <input v-model="name" class="input flex-1" placeholder="Name" required />
      <input v-model="description" class="input flex-1" placeholder="Description (optional)" />
      <button type="submit" class="btn">Add</button>
    </form>
    <p v-if="error" class="text-red-700">{{ error }}</p>
    <ul class="mt-2">
      <li v-for="item in items" :key="item.id" class="border-b border-slate-200 py-2">
        <strong>{{ item.name }}</strong>
        <span v-if="item.description" class="text-slate-500"> — {{ item.description }}</span>
      </li>
      <li v-if="items.length === 0" class="py-2 text-slate-400">No items yet.</li>
    </ul>
  </section>
</template>
