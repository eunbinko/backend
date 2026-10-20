import { beginKakaoLogin, consumeKakaoError, loadKakaoSdk, shouldShowKakaoLogin } from './kakao-login'

describe('Kakao JavaScript login', () => {
  test.each(['login', 'signup'])('shows the Kakao login action on the %s page', (page) => {
    expect(shouldShowKakaoLogin(page)).toBe(true)
  })

  test('does not show the Kakao login action outside authentication pages', () => {
    expect(shouldShowKakaoLogin('list')).toBe(false)
  })

  test('requests backend state and authorizes with nickname scope only', async () => {
    const kakao = { Auth: { authorize: jest.fn() } }
    const requestState = jest.fn().mockResolvedValue({ state: 'signed-random-state' })

    await beginKakaoLogin({ kakao, requestState, apiBase: 'http://localhost:8000' })

    expect(requestState).toHaveBeenCalledTimes(1)
    expect(kakao.Auth.authorize).toHaveBeenCalledWith({
      redirectUri: 'http://localhost:8000/user/kakao/callback',
      scope: 'profile_nickname',
      state: 'signed-random-state',
    })
  })

  test('rejects when the public JavaScript key is missing', async () => {
    await expect(loadKakaoSdk({ key: '' })).rejects.toThrow('not configured')
  })

  test('initializes an already loaded SDK once', async () => {
    const kakao = { isInitialized: () => false, init: jest.fn() }
    const sdk = await loadKakaoSdk({ key: 'public-key', windowObject: { Kakao: kakao } })
    expect(sdk).toBe(kakao)
    expect(kakao.init).toHaveBeenCalledWith('public-key')
  })

  test('consumes callback error markers from the URL', () => {
    const replaceState = jest.fn()
    const failed = consumeKakaoError({ search: '?social_error=kakao', pathname: '/login', hash: '' }, { replaceState })
    const clean = consumeKakaoError({ search: '', pathname: '/login', hash: '' }, { replaceState })
    expect(failed).toBe(true)
    expect(clean).toBe(false)
    expect(replaceState).toHaveBeenCalledWith({}, '', '/login')
  })
})
