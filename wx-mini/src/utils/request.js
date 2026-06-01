import { BASE_URL, API_PREFIX, TOKEN_KEY } from './config'

function getToken() {
  try {
    return uni.getStorageSync(TOKEN_KEY) || ''
  } catch (e) {
    return ''
  }
}

function clearTokenAndRedirect() {
  try {
    uni.removeStorageSync(TOKEN_KEY)
  } catch (e) {}
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  if (current && current.route !== 'pages/login/login') {
    uni.reLaunch({ url: '/pages/login/login' })
  }
}

function showError(msg) {
  uni.showToast({ title: msg, icon: 'none', duration: 2500 })
}

function formatDetail(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => `${(e.loc || []).join('.')} ${e.msg}`).join('; ')
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return `请求失败 ${status || ''}`
}

export function request({ url, method = 'GET', data, header = {}, raw = false }) {
  const token = getToken()
  const fullUrl = /^https?:\/\//.test(url) ? url : `${BASE_URL}${API_PREFIX}${url}`

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...header,
      },
      success: (res) => {
        const status = res.statusCode
        const body = res.data
        if (status >= 200 && status < 300) {
          resolve(raw ? res : body)
          return
        }
        const detail = body && body.detail
        if (status === 401) {
          clearTokenAndRedirect()
          reject({ status, detail, raw: res })
          return
        }
        if (status === 409) {
          // 409 业务侧自己处理（如手机号冲突）
          reject({ status, detail, raw: res })
          return
        }
        showError(formatDetail(detail, status))
        reject({ status, detail, raw: res })
      },
      fail: (err) => {
        showError('网络异常，请检查后端是否启动')
        reject({ status: 0, detail: err.errMsg, raw: err })
      },
    })
  })
}

export const http = {
  get: (url, params, options) => {
    return request({ url, method: 'GET', data: params, ...(options || {}) })
  },
  post: (url, data, options) => request({ url, method: 'POST', data, ...(options || {}) }),
  put: (url, data, options) => request({ url, method: 'PUT', data, ...(options || {}) }),
  patch: (url, data, options) => request({ url, method: 'PATCH', data, ...(options || {}) }),
  delete: (url, data, options) => request({ url, method: 'DELETE', data, ...(options || {}) }),
}

export default http
