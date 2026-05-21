import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/customers'

export const useCustomerStore = defineStore('customer', () => {
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const q = ref('')
  const loading = ref(false)
  const current = ref(null)

  async function fetchList() {
    loading.value = true
    try {
      const data = await api.listCustomers({
        q: q.value || undefined,
        page: page.value,
        page_size: pageSize.value,
      })
      items.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id) {
    current.value = await api.getCustomer(id)
    return current.value
  }

  async function create(data) {
    return api.createCustomer(data)
  }

  async function update(id, data) {
    return api.updateCustomer(id, data)
  }

  async function remove(id) {
    return api.deleteCustomer(id)
  }

  function setQuery(value) {
    q.value = value
    page.value = 1
  }

  function setPage(value) {
    page.value = value
  }

  return {
    items,
    total,
    page,
    pageSize,
    q,
    loading,
    current,
    fetchList,
    fetchDetail,
    create,
    update,
    remove,
    setQuery,
    setPage,
  }
})
