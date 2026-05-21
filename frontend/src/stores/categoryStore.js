import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/categories'

export const useCategoryStore = defineStore('category', () => {
  const list = ref([])
  const loaded = ref(false)
  const loading = ref(false)

  async function fetch(force = false) {
    if (loaded.value && !force) return list.value
    loading.value = true
    try {
      list.value = await api.listCategories()
      loaded.value = true
      return list.value
    } finally {
      loading.value = false
    }
  }

  async function create(data) {
    const obj = await api.createCategory(data)
    await fetch(true)
    return obj
  }

  async function update(code, data) {
    const obj = await api.updateCategory(code, data)
    await fetch(true)
    return obj
  }

  async function remove(code) {
    await api.deleteCategory(code)
    await fetch(true)
  }

  function labelOf(code) {
    return list.value.find((c) => c.code === code)?.label || code
  }

  return { list, loaded, loading, fetch, create, update, remove, labelOf }
})
