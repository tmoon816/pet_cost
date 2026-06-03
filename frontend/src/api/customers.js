import http from './http'

export const listCustomers = (params) => http.get('/customers', { params })
export const listRecentCustomers = (params) => http.get('/customers/recent', { params })
export const getCustomer = (id) => http.get(`/customers/${id}`)
export const getCustomerSummary = (id) => http.get(`/customers/${id}/summary`)
export const createCustomer = (data) => http.post('/customers', data)
export const updateCustomer = (id, data) => http.patch(`/customers/${id}`, data)
export const deleteCustomer = (id) => http.delete(`/customers/${id}`)

// 储值：充值、调整、流水
export const rechargeCustomer = (id, data) => http.post(`/customers/${id}/recharge`, data)
export const adjustBalance = (id, data) => http.post(`/customers/${id}/balance/adjust`, data)
export const listTransactions = (id, params) => http.get(`/customers/${id}/transactions`, { params })

export const exportCustomers = (params) => http.get('/customers/export', {
  params,
  responseType: 'blob',
})

export const downloadImportTemplate = () => http.get('/customers/import/template', {
  responseType: 'blob',
})

export const previewImport = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return http.post('/customers/import/preview', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const commitImport = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return http.post('/customers/import/commit', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
