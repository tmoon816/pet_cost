import http from './http'

export const listCustomers = (params) => http.get('/customers', { params })
export const getCustomer = (id) => http.get(`/customers/${id}`)
export const createCustomer = (data) => http.post('/customers', data)
export const updateCustomer = (id, data) => http.patch(`/customers/${id}`, data)
export const deleteCustomer = (id) => http.delete(`/customers/${id}`)
