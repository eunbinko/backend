import axios from 'axios'

const defaultApiBase = 'http://localhost:8000'

export async function fetchEsgCompanies({ fiscalYear = 2025, apiBase: baseUrl = globalThis.__ESG_API_BASE__ || defaultApiBase } = {}) {
  try {
    const response = await axios.get(`${baseUrl.replace(/\/+$/, '')}/esg/companies`, {
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
