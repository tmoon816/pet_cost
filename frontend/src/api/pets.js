import http from './http'

export const listPets = (params) => http.get('/pets', { params })
export const getPet = (id) => http.get(`/pets/${id}`)
export const createPet = (data) => http.post('/pets', data)
export const updatePet = (id, data) => http.patch(`/pets/${id}`, data)
export const deletePet = (id) => http.delete(`/pets/${id}`)
