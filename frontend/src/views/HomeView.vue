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
    <p class="status">
      Backend health:
      <span :class="['badge', health === 'ok' ? 'ok' : 'bad']">{{ health }}</span>
    </p>

    <h2>Items</h2>
    <form @submit.prevent="addItem">
      <input v-model="name" placeholder="Name" required />
      <input v-model="description" placeholder="Description (optional)" />
      <button type="submit">Add</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
    <ul>
      <li v-for="item in items" :key="item.id">
        <strong>{{ item.name }}</strong>
        <span v-if="item.description"> — {{ item.description }}</span>
      </li>
      <li v-if="items.length === 0" class="empty">No items yet.</li>
    </ul>
  </section>
</template>
