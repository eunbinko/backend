import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

globalThis.__ESG_API_BASE__ = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/+$/, '')

createApp(App).mount('#app')
