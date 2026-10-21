import { fetchEsgCompanies } from './esg'
import { api } from './client'

jest.mock('./client', () => ({ api: { get: jest.fn() } }))

describe('ESG companies API', () => {
  beforeEach(() => api.get.mockReset())

  test('requests the selected fiscal year and unwraps the standard envelope', async () => {
    const result = { fiscal_year: 2025, companies: [] }
    api.get.mockResolvedValue({ data: { code: 200, message: 'ok', result } })
    await expect(fetchEsgCompanies({ fiscalYear: 2025 })).resolves.toEqual(result)
    expect(api.get).toHaveBeenCalledWith('/esg/companies', { params: { fiscal_year: 2025 }, headers: { Accept: 'application/json' } })
  })

  test('rejects malformed response envelopes with a readable error', async () => {
    api.get.mockResolvedValue({ data: { code: 200, result: {} } })
    await expect(fetchEsgCompanies()).rejects.toThrow('기업 공시 자료 형식이 올바르지 않습니다.')
  })

  test('preserves server failure as a readable error', async () => {
    api.get.mockRejectedValue({ response: { status: 503, data: { message: '점검 중입니다.' } } })
    await expect(fetchEsgCompanies()).rejects.toThrow('점검 중입니다.')
  })
})
