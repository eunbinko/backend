import { getRoute, shouldLoadBoardList, shouldLoadCurrentUser } from './app-routing'

describe('public atlas routing', () => {
  test('opens the atlas at the public root path', () => {
    expect(getRoute('/')).toEqual({ page: 'atlas' })
  })

  test('keeps authentication and existing post routes available', () => {
    expect(getRoute('/login')).toEqual({ page: 'login' })
    expect(getRoute('/signup')).toEqual({ page: 'signup' })
    expect(getRoute('/posts/17')).toEqual({ page: 'detail', id: 17 })
  })

  test('does not load private board or user APIs for the public atlas', () => {
    expect(shouldLoadBoardList('atlas')).toBe(false)
    expect(shouldLoadCurrentUser('atlas')).toBe(false)
    expect(shouldLoadCurrentUser('login')).toBe(true)
  })
})
