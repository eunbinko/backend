export const KAKAO_CALLBACK_PATH = '/user/kakao/callback'

export function shouldShowKakaoLogin(page) {
  return page === 'login' || page === 'signup'
}

export function consumeKakaoError(location = window.location, history = window.history) {
  const params = new URLSearchParams(location.search)
  if (!params.has('social_error')) return false
  history.replaceState({}, '', `${location.pathname}${location.hash}`)
  return true
}

export function loadKakaoSdk({ key, windowObject = window, documentObject = document }) {
  if (!key) return Promise.reject(new Error('Kakao JavaScript key is not configured'))
  if (windowObject.Kakao) {
    if (!windowObject.Kakao.isInitialized()) windowObject.Kakao.init(key)
    return Promise.resolve(windowObject.Kakao)
  }

  return new Promise((resolve, reject) => {
    const existing = documentObject.querySelector('script[data-kakao-sdk]')
    const script = existing || documentObject.createElement('script')
    const loaded = () => {
      if (!windowObject.Kakao) return reject(new Error('Kakao SDK failed to initialize'))
      if (!windowObject.Kakao.isInitialized()) windowObject.Kakao.init(key)
      resolve(windowObject.Kakao)
    }
    script.addEventListener('load', loaded, { once: true })
    script.addEventListener('error', () => reject(new Error('Kakao SDK could not be loaded')), { once: true })
    if (!existing) {
      script.src = 'https://t1.kakaocdn.net/kakao_js_sdk/2.7.4/kakao.min.js'
      script.async = true
      script.dataset.kakaoSdk = 'true'
      documentObject.head.appendChild(script)
    }
  })
}

export async function beginKakaoLogin({ kakao, requestState, apiBase }) {
  const { state } = await requestState()
  kakao.Auth.authorize({
    redirectUri: `${apiBase.replace(/\/+$/, '')}${KAKAO_CALLBACK_PATH}`,
    scope: 'profile_nickname',
    state,
  })
}
