import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/categories'

export const useCategoryStore = defineStore('category', () => {
  const list = ref([])
  const loaded = ref(false)
  const loading = ref(false)

  // 兼容历史代码：原代码混用 list/categories、fetch/fetchCategories 两套命名
  // 这里全部保留，避免散点改动引入新 bug
  const categories = computed(() => list.value)

  async function fetch(force = false) {
    if (loaded.value && !force) return list.value
    loading.value = true
    try {
      list.value = await api.listCategories()
      // 按 sort_order 升序展示，与后端字段一致
      list.value.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
      loaded.value = true
      return list.value
    } finally {
      loading.value = false
    }
  }
  const fetchCategories = (force = false) => fetch(force)

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

  return {
    list,
    categories,
    loaded,
    loading,
    fetch,
    fetchCategories,
    create,
    update,
    remove,
    labelOf,
  }
})
