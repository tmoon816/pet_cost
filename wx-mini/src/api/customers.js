import http from '@/utils/request'

export const listCustomers = (params) => http.get('/customers', params)
export const listRecentCustomers = (limit = 8) => http.get('/customers/recent', { limit })
export const getCustomer = (id) => http.get(`/customers/${id}`)
export const getCustomerSummary = (id) => http.get(`/customers/${id}/summary`)
