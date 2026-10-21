import { resolveApiBaseUrl } from './base-url'

describe('API base URL configuration', () => {
  test('uses the configured backend origin directly and removes trailing slashes', () => {
    expect(resolveApiBaseUrl('https://api.kkoi.kro.kr/')).toBe('https://api.kkoi.kro.kr')
  })

  test('defaults to the production backend origin instead of a same-origin proxy', () => {
    expect(resolveApiBaseUrl(undefined)).toBe('https://api.kkoi.kro.kr')
  })
})
