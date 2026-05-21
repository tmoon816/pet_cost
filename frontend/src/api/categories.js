import http from './http'

export const listCategories = () => http.get('/categories')
export const getCategory = (code) => http.get(`/categories/${code}`)
export const createCategory = (data) => http.post('/categories', data)
export const updateCategory = (code, data) => http.patch(`/categories/${code}`, data)
export const deleteCategory = (code) => http.delete(`/categories/${code}`)
