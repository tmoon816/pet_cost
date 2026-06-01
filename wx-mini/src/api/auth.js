import http from '@/utils/request'

export const login = (data) => http.post('/auth/login', data)
export const me = () => http.get('/auth/me')
