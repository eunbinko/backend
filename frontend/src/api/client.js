import axios from 'axios'
import { resolveApiBaseUrl } from './base-url'

const baseURL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE)

export const api = axios.create({ baseURL, withCredentials: true })
