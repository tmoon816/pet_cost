import http from '@/utils/request'

export const createCost = (data) => http.post('/costs', data)
export const listCosts = (params) => http.get('/costs', params)
