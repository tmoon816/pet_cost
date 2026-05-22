import http from './http'

export const listCosts = (params) => http.get('/costs', { params })
export const getCost = (id) => http.get(`/costs/${id}`)
export const createCost = (data) => http.post('/costs', data)
export const updateCost = (id, data) => http.patch(`/costs/${id}`, data)
export const deleteCost = (id) => http.delete(`/costs/${id}`)

export const exportCosts = (params) => http.get('/costs/export', {
  params,
  responseType: 'blob',
})
