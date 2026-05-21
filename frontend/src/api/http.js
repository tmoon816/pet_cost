import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})

http.interceptors.response.use(
  (resp) => resp.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

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
