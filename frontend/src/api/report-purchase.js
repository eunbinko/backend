import { api } from './client'

export async function createReportOrder(reportId) {
  const response = await api.post(`/esg/reports/${encodeURIComponent(reportId)}/orders`, {})
  return response.data?.result
}

export async function completeReportOrder(paymentId) {
  const response = await api.post(`/esg/orders/${encodeURIComponent(paymentId)}/complete`, {})
  return response.data?.result
}
