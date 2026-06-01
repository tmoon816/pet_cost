import { defineStore } from 'pinia'
import { listCategories } from '@/api/categories'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    list: [],
    loaded: false,
    loading: false,
  }),
  getters: {
    byCode: (state) => (code) => state.list.find((c) => c.code === code),
  },
  actions: {
    async fetch(force = false) {
      if (this.loaded && !force) return this.list
      if (this.loading) return this.list
      this.loading = true
      try {
        this.list = await listCategories()
        this.loaded = true
      } finally {
        this.loading = false
      }
      return this.list
    },
  },
})
