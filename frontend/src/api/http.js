import axios from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'petcost.token'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})

// 请求拦截：注入 Bearer token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp.data,
  async (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    // 401：清登录态 + 跳登录页（懒导入避开循环依赖）
    if (status === 401) {
      try {
        const { useAuthStore } = await import('@/stores/authStore')
        const { default: router } = await import('@/router')
        useAuthStore().logout()
        const current = router.currentRoute.value
        if (current.path !== '/login') {
          router.replace({
            path: '/login',
            query: { redirect: current.fullPath },
          })
        }
      } catch {
        /* 极端异常下兜底，不阻塞错误抛出 */
      }
      return Promise.reject({ status, detail, raw: error })
    }

    // 业务侧需要拿到 detail 自己处理（如 phone 冲突弹引导框）
    if (status === 409) {
      return Promise.reject({
        status,
        detail,
        raw: error,
      })
    }

    let msg = '请求失败'
    if (typeof detail === 'string') {
      msg = detail
    } else if (Array.isArray(detail)) {
      // 422 校验错误
      msg = detail.map((e) => `${e.loc?.join('.') || ''} ${e.msg}`).join('; ')
    } else if (detail && typeof detail === 'object') {
      msg = JSON.stringify(detail)
    }
    ElMessage.error(`${status || ''} ${msg}`)
    return Promise.reject({ status, detail, raw: error })
  }
)

export default http
