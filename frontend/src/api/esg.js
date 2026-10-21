import { api } from './client'

export async function fetchEsgCompanies({ fiscalYear = 2025 } = {}) {
  try {
    const response = await api.get('/esg/companies', {
      params: { fiscal_year: fiscalYear },
      headers: { Accept: 'application/json' },
    })
    const result = response.data?.result
    if (!result || !Array.isArray(result.companies) || !Number.isInteger(result.fiscal_year)) {
      throw new Error('기업 공시 자료 형식이 올바르지 않습니다.')
    }
    return result
  } catch (error) {
    if (error.message === '기업 공시 자료 형식이 올바르지 않습니다.') throw error
    const message = error.response?.data?.message || error.response?.data?.detail
    throw new Error(typeof message === 'string' ? message : '기업 공시 자료를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')
  }
}

export async function fetchEsgReport(reportId) {
  const response = await api.get(`/esg/reports/${encodeURIComponent(reportId)}`, { headers: { Accept: 'application/json' } })
  return response.data?.result
}
