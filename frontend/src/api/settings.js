import http from './http'

export const getTierConfig = () => http.get('/settings/tiers')
export const updateTierConfig = (data) => http.put('/settings/tiers', data)
