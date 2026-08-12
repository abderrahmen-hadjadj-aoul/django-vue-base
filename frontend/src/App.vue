<script setup>
import { onMounted, ref } from 'vue'

import { api } from './api'

const health = ref('checking…')
const items = ref([])
const name = ref('')
const description = ref('')
const error = ref('')

async function loadItems() {
  const data = await api.listItems()
  // The API is paginated: results live under `results`.
  items.value = data.results ?? data
}

async function addItem() {
  if (!name.value.trim()) return
  error.value = ''
  try {
    await api.createItem({ name: name.value, description: description.value })
    name.value = ''
    description.value = ''
    await loadItems()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(async () => {
  try {
    const res = await api.health()
    health.value = res.status
    await loadItems()
  } catch (e) {
    health.value = 'unreachable'
    error.value = e.message
  }
})
</script>

<template>
  <main>
    <h1>Django + Vue Base</h1>
    <p class="status">
      Backend health:
      <span :class="['badge', health === 'ok' ? 'ok' : 'bad']">{{ health }}</span>
    </p>

    <section>
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
  </main>
</template>
