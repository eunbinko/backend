<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { beginKakaoLogin, consumeKakaoError, loadKakaoSdk, shouldShowKakaoLogin } from './kakao-login'
import EsgAtlasView from './views/EsgAtlasView.vue'
import ReportDetailView from './views/ReportDetailView.vue'
import AuthPanel from './components/AuthPanel.vue'
import { getRoute, shouldLoadCurrentUser, shouldShowAuthPage } from './app-routing'
import { api } from './api/client'

const error = ref('')
const notice = ref('')
const auth = ref({ name: '', email: '', password: '' })
const busy = ref(false)
const kakaoSdk = ref(null)
const kakaoReady = ref(false)
const kakaoError = ref('')
const kakaoBusy = ref(false)
const kakaoKey = import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY
const apiBase = api.defaults.baseURL
const route = ref(readRoute())
const currentUser = ref('')

function readRoute() { return getRoute(window.location.pathname) }

function navigate(path) {
  if (`${window.location.pathname}${window.location.search}` === path) return
  window.history.pushState({}, '', path)
  route.value = readRoute()
  error.value = ''
  notice.value = ''
  if (route.value.page === 'login' || route.value.page === 'signup') restoreCurrentUser()
}

function onPopState() {
  route.value = readRoute()
  error.value = ''
  notice.value = ''
  if (shouldLoadCurrentUser(route.value.page)) restoreCurrentUser()
}

function unwrap(data) { return data?.result ?? data }

function explainError(data, status) {
  const detail = data?.detail ?? data?.message
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ')
  if (typeof detail === 'string') return detail
  if (status === 404) return '요청한 정보를 찾지 못했습니다.'
  if (status === 409) return '이미 가입된 이메일입니다. 로그인하거나 다른 이메일을 사용하세요.'
  if (status === 401) return '이메일 또는 비밀번호를 확인하세요.'
  if (status === 422) return '입력한 내용을 확인하고 다시 시도하세요.'
  return '서버에 연결하지 못했습니다. 백엔드 실행 상태를 확인하세요.'
}

async function request(path, payload) {
  try {
    const response = payload === undefined
      ? await api.get(path, { headers: { Accept: 'application/json' } })
      : await api.post(path, payload, { headers: { Accept: 'application/json' } })
    return response.data
  } catch (cause) {
    if (cause.response) throw new Error(explainError(cause.response.data, cause.response.status))
    throw new Error('백엔드 서버에 연결하지 못했습니다. 백엔드 실행 상태를 확인하세요.')
  }
}

async function submitAuth() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const mode = route.value.page === 'signup' ? 'signup' : 'login'
    const payload = mode === 'signup'
      ? { name: auth.value.name.trim(), email: auth.value.email.trim(), password: auth.value.password }
      : { email: auth.value.email.trim(), password: auth.value.password }
    const user = unwrap(await request(`/user/${mode}`, payload))
    if (mode === 'signup') {
      auth.value.password = ''
      navigate('/login')
      notice.value = `${user.name}님, 가입이 완료됐습니다. 로그인해 주세요.`
      return
    }

    currentUser.value = user.name
    auth.value.password = ''
    const next = route.value.next
    const nextPath = next?.startsWith('/') && !next.startsWith('//') ? next : '/'
    navigate(nextPath)
    notice.value = `${user.name}님, 로그인했습니다.`
  } catch (cause) {
    error.value = cause.message
  } finally {
    busy.value = false
  }
}

async function startKakaoLogin() {
  if (kakaoBusy.value || !kakaoSdk.value) return
  kakaoBusy.value = true
  kakaoError.value = ''
  try {
    await beginKakaoLogin({
      kakao: kakaoSdk.value,
      apiBase,
      requestState: async () => {
        const response = await api.post('/user/kakao/state', {}, { headers: { Accept: 'application/json' } })
        return response.data.result
      },
    })
  } catch {
    kakaoError.value = '카카오 로그인을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요.'
    kakaoBusy.value = false
  }
}

async function restoreCurrentUser() {
  try {
    const user = unwrap(await request('/user/me'))
    currentUser.value = user?.name || ''
  } catch {
    currentUser.value = ''
  }
}

async function logout() {
  if (busy.value) return
  busy.value = true
  try {
    await request('/user/logout', {})
    currentUser.value = ''
    auth.value.password = ''
    navigate('/login')
    notice.value = '로그아웃되었습니다.'
  } catch (cause) {
    error.value = cause.message
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  window.addEventListener('popstate', onPopState)
  if (shouldLoadCurrentUser(route.value.page)) restoreCurrentUser()
  if (shouldShowKakaoLogin(route.value.page)) loadKakaoSdk({ key: kakaoKey }).then((sdk) => {
    kakaoSdk.value = sdk
    kakaoReady.value = true
  }).catch(() => {
    kakaoError.value = '카카오 로그인을 사용할 수 없습니다. JavaScript 키와 SDK 연결을 확인해 주세요.'
  })
  if (route.value.page === 'login' && consumeKakaoError()) {
    error.value = '카카오 로그인에 실패했습니다. 다시 시도해 주세요.'
  }
})
onUnmounted(() => window.removeEventListener('popstate', onPopState))
</script>

<template>
  <EsgAtlasView v-if="route.page === 'atlas'" />
  <template v-else>
    <a class="skip-link" href="#main">본문으로 건너뛰기</a>
    <header class="topbar">
      <a class="brand" href="/" aria-label="공시 아틀라스 홈" @click.prevent="navigate('/')">
        <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span><span>공시 아틀라스</span>
      </a>
      <nav class="top-actions" aria-label="주요 메뉴">
        <a class="nav-link" href="/" @click.prevent="navigate('/')">공시 지도</a>
        <a v-if="currentUser" class="account-button" href="/" @click.prevent="navigate('/')"><span class="avatar" aria-hidden="true">{{ currentUser.slice(0, 1) }}</span><span>{{ currentUser }}</span></a>
        <a v-else class="account-button" href="/login" @click.prevent="navigate('/login')"><span class="avatar" aria-hidden="true">나</span><span>로그인</span></a>
        <button v-if="currentUser" class="logout-button" type="button" :disabled="busy" @click="logout">로그아웃</button>
      </nav>
    </header>

    <ReportDetailView v-if="route.page === 'report'" :report-id="route.id" :navigate="navigate" />
    <main v-else-if="shouldShowAuthPage(route.page)" id="main" class="auth-route">
      <AuthPanel :mode="route.page" :model="auth" :busy="busy" :error="error || kakaoError" :notice="notice" @submit="submitAuth" @navigate="navigate">
        <template #social>
          <div v-if="shouldShowKakaoLogin(route.page)" class="social-login">
            <button class="kakao-button" type="button" :disabled="!kakaoReady || kakaoBusy" @click="startKakaoLogin">
              {{ kakaoBusy ? '카카오 로그인 연결 중…' : '카카오로 로그인' }}
            </button>
          </div>
        </template>
      </AuthPanel>
    </main>
  </template>
</template>
