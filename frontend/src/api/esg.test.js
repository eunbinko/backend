import { fetchEsgCompanies } from './esg'
import axios from 'axios'

jest.mock('axios', () => ({ get: jest.fn() }))

describe('ESG companies API', () => {
  beforeEach(() => axios.get.mockReset())

  test('requests the selected fiscal year and unwraps the standard envelope', async () => {
    const result = { fiscal_year: 2025, companies: [] }
    axios.get.mockResolvedValue({ data: { code: 200, message: 'ok', result } })
    await expect(fetchEsgCompanies({ fiscalYear: 2025, apiBase: 'http://api.test/' })).resolves.toEqual(result)
    expect(axios.get).toHaveBeenCalledWith('http://api.test/esg/companies', { params: { fiscal_year: 2025 }, headers: { Accept: 'application/json' }, withCredentials: true })
  })

  test('rejects malformed response envelopes with a readable error', async () => {
    axios.get.mockResolvedValue({ data: { code: 200, result: {} } })
    await expect(fetchEsgCompanies()).rejects.toThrow('기업 공시 자료 형식이 올바르지 않습니다.')
  })

  test('preserves server failure as a readable error', async () => {
    axios.get.mockRejectedValue({ response: { status: 503, data: { message: '점검 중입니다.' } } })
    await expect(fetchEsgCompanies()).rejects.toThrow('점검 중입니다.')
  })
})
