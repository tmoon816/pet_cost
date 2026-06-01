import http from '@/utils/request'

export const listCategories = () => http.get('/categories')
