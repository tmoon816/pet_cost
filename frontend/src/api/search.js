import http from './http'

export const search = (q) => http.get('/search', { params: { q } })