import { getOfficialReportUrl, hasOfficialPdf } from './report-links'

describe('official ESG report links', () => {
  test('opens the PDF viewer only when a verified HTTPS PDF URL exists', () => {
    expect(hasOfficialPdf({ pdf_url: 'https://issuer.example/report.pdf' })).toBe(true)
    expect(hasOfficialPdf({ pdf_url: null })).toBe(false)
    expect(hasOfficialPdf({ pdf_url: 'http://issuer.example/report.pdf' })).toBe(false)
  })

  test('falls back to the official report page when the issuer does not expose a direct PDF URL', () => {
    expect(getOfficialReportUrl({ landing_page_url: 'https://issuer.example/reports' })).toBe('https://issuer.example/reports')
    expect(getOfficialReportUrl({ source_url: 'https://exchange.example/filing' })).toBe('https://exchange.example/filing')
    expect(getOfficialReportUrl({})).toBeNull()
  })
})
