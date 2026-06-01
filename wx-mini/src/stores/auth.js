import { defineStore } from 'pinia'
import { login as apiLogin, me as apiMe } from '@/api/auth'
import { TOKEN_KEY } from '@/utils/config'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: uni.getStorageSync(TOKEN_KEY) || '',
    username: '',
  }),
  getters: {
    isLogin: (state) => Boolean(state.token),
  },
  actions: {
    async login(payload) {
      const data = await apiLogin(payload)
      this.token = data.access_token
      uni.setStorageSync(TOKEN_KEY, data.access_token)
      try {
        const info = await apiMe()
        this.username = info.username
      } catch (e) {
        // /me 失败不阻塞登录
      }
    },
    logout() {
      this.token = ''
      this.username = ''
      try {
        uni.removeStorageSync(TOKEN_KEY)
      } catch (e) {}
    },
  },
})
