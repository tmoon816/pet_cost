import http from './http'

export const getSummary = (params) => http.get('/stats/summary', { params })
export const getCashflow = (params) => http.get('/stats/cashflow', { params })
export const getByCategory = (params) => http.get('/stats/by-category', { params })
export const getByMonth = (params) => http.get('/stats/by-month', { params })
export const getByDay = (params) => http.get('/stats/by-day', { params })
export const getByPet = (params) => http.get('/stats/by-pet', { params })
export const getCustomerAcquisition = (params) => http.get('/stats/customer-acquisition', { params })
export const getDormantCustomers = (params) => http.get('/stats/dormant-customers', { params })
export const getTopCustomers = (params) => http.get('/stats/top-customers', { params })
