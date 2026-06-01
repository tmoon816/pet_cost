import http from '@/utils/request'

export const getSummary = (params) => http.get('/stats/summary', params)
