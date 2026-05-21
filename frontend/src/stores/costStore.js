import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/costs'

export const useCostStore = defineStore('cost', () => {
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const filters = ref({
    pet_id: null,
    customer_id: null,
    category: null,
    start: null,
    end: null,
  })
  const loading = ref(false)

  function _params() {
    const p = { page: page.value, page_size: pageSize.value }
    for (const [k, v] of Object.entries(filters.value)) {
      if (v !== null && v !== undefined && v !== '') p[k] = v
    }
    return p
  }

  async function fetchList() {
    loading.value = true
    try {
      const data = await api.listCosts(_params())
      items.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  function setFilters(next) {
    filters.value = { ...filters.value, ...next }
    page.value = 1
  }

  function resetFilters() {
    filters.value = {
      pet_id: null,
      customer_id: null,
      category: null,
      start: null,
      end: null,
    }
    page.value = 1
  }

  function setPage(value) {
    page.value = value
  }

  async function create(data) {
    return api.createCost(data)
  }
  async function update(id, data) {
    return api.updateCost(id, data)
  }
  async function remove(id) {
    return api.deleteCost(id)
  }

  return {
    items,
    total,
    page,
    pageSize,
    filters,
    loading,
    fetchList,
    setFilters,
    resetFilters,
    setPage,
    create,
    update,
    remove,
  }
})
