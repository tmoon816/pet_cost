import http from './http'

export const listBudgets = (params) => http.get('/budgets', { params })
export const getBudget = (id) => http.get(`/budgets/${id}`)
export const createBudget = (data) => http.post('/budgets', data)
export const updateBudget = (id, data) => http.patch(`/budgets/${id}`, data)
export const deleteBudget = (id) => http.delete(`/budgets/${id}`)
