import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/pets'

export const usePetStore = defineStore('pet', () => {
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const current = ref(null)

  async function fetchByCustomer(customerId) {
    loading.value = true
    try {
      const data = await api.listPets({ customer_id: customerId, page: 1, page_size: 100 })
      items.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id) {
    current.value = await api.getPet(id)
    return current.value
  }

  async function create(data) {
    return api.createPet(data)
  }

  async function update(id, data) {
    return api.updatePet(id, data)
  }

  async function remove(id) {
    return api.deletePet(id)
  }

  return { items, total, loading, current, fetchByCustomer, fetchDetail, create, update, remove }
})
