import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/customers'

export const useCustomerStore = defineStore('customer', () => {
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const q = ref('')
  const sortBy = ref(null) // T-015: null 默认 created_at；'total_amount' 按累计金额
  const sortDir = ref('desc')
  const loading = ref(false)
  const current = ref(null)

  async function fetchList() {
    loading.value = true
    try {
      const data = await api.listCustomers({
        q: q.value || undefined,
        page: page.value,
        page_size: pageSize.value,
        sort_by: sortBy.value || undefined,
        sort_dir: sortBy.value ? sortDir.value : undefined,
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

  // T-015：切换排序。传 null 恢复默认（created_at）；同一列重复点击在 desc/asc 间切换
  function setSort(by) {
    if (by === null || by === undefined) {
      sortBy.value = null
      sortDir.value = 'desc'
    } else if (sortBy.value === by) {
      sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
    } else {
      sortBy.value = by
      sortDir.value = 'desc'
    }
    page.value = 1
  }

  return {
    items,
    total,
    page,
    pageSize,
    q,
    sortBy,
    sortDir,
    loading,
    current,
    fetchList,
    fetchDetail,
    create,
    update,
    remove,
    setQuery,
    setPage,
    setSort,
  }
})
