import axios from 'axios'

const baseURL = (import.meta.env.VITE_API_BASE || 'https://api.kkoi.kro.kr').replace(/\/+$/, '')

export const api = axios.create({ baseURL, withCredentials: true })
