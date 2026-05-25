import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/auth'

const TOKEN_KEY = 'petcost.token'
const USERNAME_KEY = 'petcost.username'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const username = ref(localStorage.getItem(USERNAME_KEY) || '')

  const isAuthenticated = computed(() => !!token.value)

  function _persist(t, u) {
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
    if (u) localStorage.setItem(USERNAME_KEY, u)
    else localStorage.removeItem(USERNAME_KEY)
  }

  async function login(name, password) {
    const data = await api.login({ username: name, password })
    token.value = data.access_token
    username.value = name
    _persist(token.value, username.value)
    return data
  }

  function logout() {
    token.value = ''
    username.value = ''
    _persist('', '')
  }

  // 启动时校验 localStorage 里的 token 是否还有效
  async function restore() {
    if (!token.value) return false
    try {
      const me = await api.me()
      username.value = me.username
      _persist(token.value, username.value)
      return true
    } catch {
      logout()
      return false
    }
  }

  return { token, username, isAuthenticated, login, logout, restore }
})
