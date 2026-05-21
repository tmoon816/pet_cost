import http from './http'

export const statsSummary = (params) => http.get('/stats/summary', { params })
export const statsByCategory = (params) => http.get('/stats/by-category', { params })
export const statsByMonth = (params) => http.get('/stats/by-month', { params })
export const statsByPet = (params) => http.get('/stats/by-pet', { params })
