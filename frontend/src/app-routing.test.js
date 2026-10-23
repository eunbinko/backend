import { getRoute, shouldLoadCurrentUser, shouldShowAuthPage } from './app-routing'

describe('public atlas routing', () => {
  test('opens the atlas at the public root path', () => {
    expect(getRoute('/')).toEqual({ page: 'atlas' })
  })

  test('keeps authentication routes available and retires memo routes', () => {
    expect(getRoute('/login')).toEqual({ page: 'login', next: null })
    expect(getRoute('/signup')).toEqual({ page: 'signup' })
    expect(getRoute('/write')).toEqual({ page: 'atlas' })
    expect(getRoute('/posts/17')).toEqual({ page: 'atlas' })
  })

  test('supports stable report detail URLs', () => {
    expect(getRoute('/reports')).toEqual({ page: 'atlas' })
    expect(getRoute('/reports/23')).toEqual({ page: 'report', id: 23 })
  })

  test('shows authentication only on authentication routes, never report routes', () => {
    expect(shouldShowAuthPage('login')).toBe(true)
    expect(shouldShowAuthPage('signup')).toBe(true)
    expect(shouldShowAuthPage('report')).toBe(false)
    expect(getRoute('/reports/23').page).toBe('report')
  })

  test('loads the current user for reports and authentication routes, not the public atlas', () => {
    expect(shouldLoadCurrentUser('atlas')).toBe(false)
    expect(shouldLoadCurrentUser('login')).toBe(true)
    expect(shouldLoadCurrentUser('report')).toBe(true)
  })
})
