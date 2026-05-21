import http from './http'

export const getSummary = (params) => http.get('/stats/summary', { params })
export const getByCategory = (params) => http.get('/stats/by-category', { params })
export const getByMonth = (params) => http.get('/stats/by-month', { params })
export const getByPet = (params) => http.get('/stats/by-pet', { params })
