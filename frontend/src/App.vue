<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { beginKakaoLogin, consumeKakaoError, loadKakaoSdk, shouldShowKakaoLogin } from './kakao-login'
import EsgAtlasView from './views/EsgAtlasView.vue'
import ReportDetailView from './views/ReportDetailView.vue'
import { getRoute, shouldLoadBoardList, shouldLoadCurrentUser } from './app-routing'

const apiBase = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/+$/, '')
const boards = ref([])
const selected = ref(null)
const loading = ref(false)
const pageLoading = ref(false)
const error = ref('')
const notice = ref('')
const authMode = ref('login')
const auth = ref({ name: '', email: '', password: '' })
const post = ref({ title: '', contents: '' })
const busy = ref(false)
const busyAction = ref('')
const kakaoSdk = ref(null)
const kakaoReady = ref(false)
const kakaoError = ref('')
const kakaoBusy = ref(false)
const kakaoKey = import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY
const route = ref(readRoute())
let routeTimer

function readRoute() { return getRoute(window.location.pathname) }

const sortedBoards = computed(() => [...boards.value].sort((a, b) => b.idx - a.idx))
const currentUser = ref('')

function navigate(path) {
  if (`${window.location.pathname}${window.location.search}` === path) return
  window.history.pushState({}, '', path)
  route.value = readRoute()
  error.value = ''
  notice.value = ''
  pageLoading.value = true
  clearTimeout(routeTimer)
  routeTimer = setTimeout(() => { pageLoading.value = false }, 280)
  if (route.value.page === 'detail') openBoard(route.value.id)
  if (route.value.page === 'report') selected.value = null
  if (route.value.page === 'atlas') selected.value = null
  if (route.value.page === 'login' || route.value.page === 'signup') authMode.value = route.value.page
}

function onPopState() {
  route.value = readRoute()
  error.value = ''
  pageLoading.value = true
  clearTimeout(routeTimer)
  routeTimer = setTimeout(() => { pageLoading.value = false }, 280)
  if (route.value.page === 'detail') openBoard(route.value.id)
  else selected.value = null
}

function unwrap(data) { return data?.result ?? data }

function explainError(data, status) {
  const detail = data?.detail ?? data?.message
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ')
  if (typeof detail === 'string') return detail
  if (status === 404) return '요청한 기록을 찾지 못했습니다.'
  if (status === 409) return '이미 가입된 이메일입니다. 로그인하거나 다른 이메일을 사용하세요.'
  if (status === 401) return '이메일 또는 비밀번호를 확인하세요.'
  if (status === 422) return '입력한 내용을 확인하고 다시 시도하세요.'
  return '서버에 연결하지 못했습니다. 백엔드 실행 상태를 확인하세요.'
}

async function request(path, payload) {
  const response = await fetch(`${apiBase}${path}`, {
    method: payload === undefined ? 'GET' : 'POST',
    credentials: 'include',
    headers: payload === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
    ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
  })
  let data
  try { data = await response.json() } catch { throw new Error('서버 응답을 읽지 못했습니다. API 주소를 확인하세요.') }
  if (!response.ok) throw new Error(explainError(data, response.status))
  return data
}

async function loadBoards() {
  loading.value = true
  error.value = ''
  try {
    const data = await request('/board')
    boards.value = Array.isArray(unwrap(data)) ? unwrap(data) : []
  } catch (cause) { error.value = cause.message } finally { loading.value = false }
}

async function openBoard(id) {
  selected.value = null
  try {
    const data = await request(`/board/read/${encodeURIComponent(id)}`)
    selected.value = unwrap(data)
  } catch (cause) { error.value = cause.message }
}

async function publish() {
  if (busy.value) return
  busy.value = true; busyAction.value = 'write'; error.value = ''; notice.value = ''
  try {
    const data = await request('/board/register', { title: post.value.title.trim(), contents: post.value.contents.trim() })
    const created = unwrap(data)
    post.value = { title: '', contents: '' }
    await loadBoards()
    selected.value = created
    notice.value = '기록을 저장했습니다.'
    navigate(`/posts/${created.idx}`)
  } catch (cause) { error.value = cause.message } finally { busy.value = false; busyAction.value = '' }
}

async function submitAuth() {
  if (busy.value) return
  busy.value = true; busyAction.value = 'auth'; error.value = ''; notice.value = ''
  try {
    const mode = route.value.page === 'signup' ? 'signup' : 'login'
    const payload = mode === 'signup'
      ? { name: auth.value.name.trim(), email: auth.value.email.trim(), password: auth.value.password }
      : { email: auth.value.email.trim(), password: auth.value.password }
    const data = await request(`/user/${mode}`, payload)
    const user = unwrap(data)
    notice.value = mode === 'signup' ? `${user.name}님, 가입이 완료됐습니다. 로그인해 주세요.` : `${user.name}님, 로그인했습니다.`
    if (mode === 'signup') {
      auth.value.password = ''
      navigate('/login')
      notice.value = `${user.name}님, 가입이 완료됐습니다. 로그인해 주세요.`
    } else {
      currentUser.value = user.name
      auth.value.password = ''
      const next = route.value.next
      navigate(next && next.startsWith('/') ? next : '/')
      notice.value = `${user.name}님, 로그인했습니다.`
    }
  } catch (cause) { error.value = cause.message } finally { busy.value = false; busyAction.value = '' }
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
        const response = await fetch(`${apiBase}/user/kakao/state`, {
          method: 'POST', credentials: 'include', headers: { Accept: 'application/json' },
        })
        const data = await response.json()
        if (!response.ok) throw new Error('Kakao login could not be started')
        return data.result
      },
    })
  } catch {
    kakaoError.value = '카카오 로그인을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요.'
    kakaoBusy.value = false
  }
}

async function restoreCurrentUser() {
  try {
    const data = await request('/user/me')
    currentUser.value = unwrap(data)?.name || ''
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

function formatNumber(value) { return new Intl.NumberFormat('ko-KR').format(value) }

onMounted(() => {
  window.addEventListener('popstate', onPopState)
  if (shouldLoadCurrentUser(route.value.page)) restoreCurrentUser()
  if (shouldLoadBoardList(route.value.page)) loadBoards()
  if (route.value.page === 'detail') openBoard(route.value.id)
  if (route.value.page === 'login' || route.value.page === 'signup') authMode.value = route.value.page
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
onUnmounted(() => { window.removeEventListener('popstate', onPopState); clearTimeout(routeTimer) })
</script>

<template>
  <EsgAtlasView v-if="route.page === 'atlas'" />
  <ReportDetailView v-if="route.page === 'report'" :report-id="route.id" :navigate="navigate" />
  <a class="skip-link" href="#main">본문으로 건너뛰기</a>
  <header v-if="route.page !== 'atlas'" class="topbar">
    <a class="brand" href="/" aria-label="모아 홈" @click.prevent="navigate('/')">
      <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span><span>모아</span>
    </a>
    <nav class="top-actions" aria-label="주요 메뉴">
      <a class="nav-link" href="/" @click.prevent="navigate('/')">기록 모아보기</a>
      <a v-if="currentUser" class="account-button" href="/" @click.prevent="navigate('/')"><span class="avatar" aria-hidden="true">{{ currentUser.slice(0, 1) }}</span><span>{{ currentUser }}</span></a>
      <a v-else class="account-button" href="/login" @click.prevent="navigate('/login')"><span class="avatar" aria-hidden="true">나</span><span>로그인</span></a>
    </nav>
  </header>

  <main v-if="route.page !== 'atlas'" id="main" class="page-shell" :class="`page-${route.page}`">
    <section class="masthead">
      <div class="masthead-copy">
        <p class="edition">모아의 기록장 <span class="edition-rule"></span> 작은 생각을 오래 읽도록</p>
        <h1>오늘의 생각을<br />한곳에 모아요.</h1>
        <p class="lede">지나가는 생각을 적고, 마음에 남은 문장을 다시 읽어보세요.</p>
      </div>
      <div class="masthead-note" aria-hidden="true"><svg viewBox="0 0 180 150" fill="none"><path d="M26 117c20-18 21-53 36-75 9-14 24-22 36-15 13 8 6 31-1 47-11 24-23 50-12 59 12 10 37-16 51-35 12-16 19-31 30-39" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><path d="M145 58c10-7 17-6 23-2" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><circle cx="39" cy="48" r="4" fill="currentColor"/><circle cx="132" cy="122" r="3" fill="currentColor"/></svg></div>
      <a class="write-button" href="/write" @click.prevent="navigate('/write')"><span class="plus" aria-hidden="true">+</span> 새 기록 쓰기</a>
    </section>

    <Transition name="page" mode="out-in">
      <div :key="route.page + (route.id || '')" class="page-content">
        <div v-if="pageLoading" class="content-layout" aria-label="페이지 불러오는 중" aria-busy="true">
          <section class="feed"><div class="feed-heading"><div><span class="skeleton skeleton-label"></span><span class="skeleton skeleton-title"></span></div><span class="skeleton skeleton-count"></span></div><div class="skeleton-list"><div v-for="n in 4" :key="n" class="skeleton-row"><span class="skeleton skeleton-number"></span><div><span class="skeleton skeleton-line wide"></span><span class="skeleton skeleton-line"></span></div></div></div></section>
          <aside class="side-panel skeleton-panel"><span class="skeleton skeleton-label"></span><span class="skeleton skeleton-title"></span><span v-for="n in 3" :key="n" class="skeleton skeleton-input"></span><span class="skeleton skeleton-submit"></span></aside>
        </div>

        <div v-else-if="route.page === 'list'" class="content-layout">
          <section class="feed" aria-labelledby="feed-title">
            <div class="feed-heading"><div><p class="section-kicker">모아 둔 글</p><h2 id="feed-title">기록 모아보기</h2></div><span class="count">{{ formatNumber(boards.length) }}개의 기록</span></div>
            <div v-if="loading" class="post-list" aria-label="기록 불러오는 중" aria-busy="true"><div v-for="n in 4" :key="n" class="skeleton-row"><span class="skeleton skeleton-number"></span><div><span class="skeleton skeleton-line wide"></span><span class="skeleton skeleton-line"></span></div></div></div>
            <div v-else-if="error" class="state-message error-state" role="alert"><strong>기록을 가져오지 못했습니다.</strong><span>{{ error }}</span><button type="button" class="text-button" @click="loadBoards">다시 불러오기</button></div>
            <div v-else-if="sortedBoards.length === 0" class="empty-state"><span class="empty-symbol" aria-hidden="true">✳</span><h3>아직 모인 기록이 없어요.</h3><p>첫 번째 생각을 적어 이곳에 남겨보세요.</p><a class="text-button" href="/write" @click.prevent="navigate('/write')">첫 기록 쓰기</a></div>
            <ol v-else class="post-list"><li v-for="board in sortedBoards" :key="board.idx"><a class="post-row" :href="`/posts/${board.idx}`" @click.prevent="navigate(`/posts/${board.idx}`)"><span class="post-index">{{ String(board.idx).padStart(2, '0') }}</span><span class="post-copy"><strong>{{ board.title }}</strong><span>{{ board.contents }}</span></span><span class="post-open" aria-hidden="true">↗</span></a></li></ol>
          </section>
          <aside class="side-column"><section class="side-panel prompt-panel"><span class="prompt-mark" aria-hidden="true">“</span><p class="section-kicker">기록의 시작</p><h2>작은 문장 하나가<br />내일의 생각이 됩니다.</h2><p>잘 쓴 글이 아니어도 괜찮아요. 오늘의 마음을 편하게 적어보세요.</p><a class="quiet-button" href="/write" @click.prevent="navigate('/write')">기록 시작하기</a></section><p class="side-footnote"><span class="footnote-dot"></span><span>기록은 이 공간에 차곡차곡 쌓입니다.</span></p></aside>
        </div>

        <div v-else-if="route.page === 'detail'" class="single-layout">
          <article v-if="selected" class="article-page"><a class="back-link" href="/" @click.prevent="navigate('/')">← 기록 모아보기</a><p class="section-kicker">기록 {{ formatNumber(selected.idx) }}</p><h2>{{ selected.title }}</h2><div class="article-rule"></div><p class="article-body">{{ selected.contents }}</p></article>
          <div v-else-if="error" class="state-message error-state" role="alert"><strong>기록을 열지 못했습니다.</strong><span>{{ error }}</span><a class="text-button" href="/" @click.prevent="navigate('/')">목록으로 돌아가기</a></div>
          <div v-else class="article-page" aria-busy="true"><span class="skeleton skeleton-label"></span><span class="skeleton article-skeleton-title"></span><span class="skeleton skeleton-line wide"></span><span v-for="n in 7" :key="n" class="skeleton article-skeleton-line"></span></div>
        </div>

        <div v-else-if="route.page === 'write'" class="single-layout">
          <section class="form-page" aria-labelledby="write-title"><a class="back-link" href="/" @click.prevent="navigate('/')">← 기록 모아보기</a><p class="section-kicker">새 기록</p><h2 id="write-title">지금 떠오른 생각</h2><p class="form-intro">짧은 메모도 좋아요. 제목과 내용을 적어주세요.</p><form class="stack-form" @submit.prevent="publish"><label for="post-title">제목</label><input id="post-title" v-model="post.title" name="title" maxlength="200" required placeholder="어떤 생각인가요?" /><label for="post-contents">내용</label><textarea id="post-contents" v-model="post.contents" name="contents" rows="10" required placeholder="여기에 기록을 남겨보세요"></textarea><p v-if="error" class="inline-error" role="alert">{{ error }}</p><button class="solid-button" type="submit" :disabled="busy">{{ busy && busyAction === 'write' ? '저장 중…' : '기록 저장하기' }}</button></form></section>
        </div>

        <div v-else class="single-layout auth-layout">
          <section class="form-page auth-page" :aria-labelledby="route.page === 'signup' ? 'signup-title' : 'login-title'"><p class="section-kicker">{{ route.page === 'signup' ? '처음 오셨나요' : '다시 만났네요' }}</p><h2 :id="route.page === 'signup' ? 'signup-title' : 'login-title'">{{ route.page === 'signup' ? '함께 기록해요.' : '기록을 이어가세요.' }}</h2><p class="form-intro">{{ route.page === 'signup' ? '이름과 이메일로 계정을 만들어요.' : '가입한 계정으로 로그인하세요.' }}</p><form class="stack-form" @submit.prevent="submitAuth"><label v-if="route.page === 'signup'" for="account-name">이름</label><input v-if="route.page === 'signup'" id="account-name" v-model="auth.name" name="name" autocomplete="name" required placeholder="이름을 입력하세요" /><label for="account-email">이메일</label><input id="account-email" v-model="auth.email" name="email" type="email" autocomplete="username" spellcheck="false" required placeholder="hello@example.com" /><label for="account-password">비밀번호</label><input id="account-password" v-model="auth.password" name="password" type="password" :autocomplete="route.page === 'login' ? 'current-password' : 'new-password'" minlength="1" maxlength="128" required placeholder="비밀번호를 입력하세요" /><p v-if="error" class="inline-error" role="alert">{{ error }}</p><p v-if="notice" class="inline-notice" role="status">{{ notice }}</p><button class="solid-button" type="submit" :disabled="busy">{{ busy ? '처리 중…' : route.page === 'signup' ? '가입하기' : '로그인' }}</button></form><p class="form-switch">{{ route.page === 'signup' ? '이미 계정이 있나요?' : '아직 계정이 없나요?' }} <a :href="route.page === 'signup' ? '/login' : '/signup'" @click.prevent="navigate(route.page === 'signup' ? '/login' : '/signup')">{{ route.page === 'signup' ? '로그인' : '회원가입' }}</a></p></section>
        </div>
      </div>
    </Transition>
    <footer class="page-footer"><span>모아</span><span>생각을 담아두는 곳</span></footer>
  </main>
  <Teleport v-if="shouldShowKakaoLogin(route.page)" to=".auth-page">
    <div class="social-login">
      <span class="social-divider">또는</span>
      <p v-if="kakaoError" class="inline-error" role="alert">{{ kakaoError }}</p>
      <button class="kakao-button" type="button" :disabled="!kakaoReady || kakaoBusy" @click="startKakaoLogin">
        {{ kakaoBusy ? '카카오 로그인 연결 중…' : '카카오로 로그인' }}
      </button>
    </div>
  </Teleport>
  <Teleport v-if="currentUser" to=".top-actions">
    <button class="logout-button" type="button" :disabled="busy" @click="logout">로그아웃</button>
  </Teleport>
</template>
