import http from './http'

// 寄养单
export const listBoarding = (params) => http.get('/boarding', { params })
export const createBoarding = (data) => http.post('/boarding', data)
export const closeBoarding = (id, data) => http.post(`/boarding/${id}/close`, data)
export const settleBoarding = () => http.post('/boarding/settle')
export const deleteBoarding = (id) => http.delete(`/boarding/${id}`)
export const getBoardingAlerts = () => http.get('/boarding/alerts')
