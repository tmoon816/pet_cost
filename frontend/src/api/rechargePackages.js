import http from './http'

// 充值套餐
export const listPackages = (params) => http.get('/recharge-packages', { params })
export const createPackage = (data) => http.post('/recharge-packages', data)
export const updatePackage = (id, data) => http.patch(`/recharge-packages/${id}`, data)
export const deletePackage = (id) => http.delete(`/recharge-packages/${id}`)
export const checkoutPackage = (id, data) => http.post(`/recharge-packages/${id}/checkout`, data)
