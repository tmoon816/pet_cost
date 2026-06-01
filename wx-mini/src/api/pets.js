import http from '@/utils/request'

export const listPets = (params) => http.get('/pets', params)
export const getPet = (id) => http.get(`/pets/${id}`)
