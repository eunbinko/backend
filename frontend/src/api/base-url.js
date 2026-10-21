const DEFAULT_API_BASE_URL = 'https://api.kkoi.kro.kr'

export function resolveApiBaseUrl(configuredBaseUrl) {
  return (configuredBaseUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, '')
}
