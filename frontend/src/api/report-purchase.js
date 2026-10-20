import axios from 'axios'

const apiBase = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/+$/, '')

export async function createReportOrder(reportId) {
  const response = await axios.post(`${apiBase}/esg/reports/${encodeURIComponent(reportId)}/orders`, {}, { withCredentials: true })
  return response.data?.result
}

export async function completeReportOrder(paymentId) {
  const response = await axios.post(`${apiBase}/esg/orders/${encodeURIComponent(paymentId)}/complete`, {}, { withCredentials: true })
  return response.data?.result
}
