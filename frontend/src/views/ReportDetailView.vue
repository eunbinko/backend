<script setup>
import { onMounted, ref } from 'vue'
import { fetchEsgReport } from '../api/esg'
import { completeReportOrder, createReportOrder } from '../api/report-purchase'
import { requestReportPayment } from '../portone-payment'
import { api } from '../api/client'

const props = defineProps({ reportId: { type: Number, required: true }, navigate: { type: Function, required: true } })
const report = ref(null)
const busy = ref(false)
const error = ref('')
const notice = ref('')
const currentUser = ref(null)

async function loadCurrentUser() {
  try {
    const response = await api.get('/user/me', { headers: { Accept: 'application/json' } })
    currentUser.value = response.data?.result || null
  } catch { currentUser.value = null }
}

async function load() {
  try { report.value = await fetchEsgReport(props.reportId) } catch (cause) { error.value = cause.message || '보고서를 불러오지 못했습니다.' }
}

async function buy() {
  if (busy.value || !report.value?.price_krw) return
  if (!currentUser.value) { props.navigate(`/login?next=${encodeURIComponent(`/reports/${props.reportId}`)}`); return }
  busy.value = true; error.value = ''; notice.value = ''
  try {
    const order = await createReportOrder(props.reportId)
    const result = await requestReportPayment(order, window.location.href)
    if (result?.code) { notice.value = '결제가 취소되었거나 완료되지 않았습니다. 다시 시도할 수 있습니다.'; return }
    if (result?.paymentId) {
      await completeReportOrder(result.paymentId)
      await load()
      notice.value = '결제가 확인되었습니다.'
    }
  } catch (cause) { error.value = cause.response?.data?.message || cause.message || '결제를 완료하지 못했습니다.' }
  finally { busy.value = false }
}

async function confirmRedirect() {
  const query = new URLSearchParams(window.location.search)
  const paymentId = query.get('paymentId')
  if (!paymentId || query.has('code')) return
  try { await completeReportOrder(paymentId); await load(); notice.value = '결제가 확인되었습니다.' }
  catch (cause) { error.value = cause.response?.data?.message || '결제를 확인하지 못했습니다.' }
  finally { window.history.replaceState({}, '', window.location.pathname) }
}

onMounted(async () => { await loadCurrentUser(); await load(); await confirmRedirect() })
</script>

<template>
  <main class="report-detail-page">
    <a class="report-back" href="/" @click.prevent="navigate('/')">← 지도 돌아가기</a>
    <article v-if="report" class="report-summary-card">
      <p class="atlas-kicker">{{ report.company_name }} · {{ report.report_year }} 공시</p>
      <h1>{{ report.title }}</h1>
      <p class="report-summary">{{ report.summary }}</p>
      <dl class="report-metadata"><div><dt>페이지 수</dt><dd>{{ report.page_count ? `${report.page_count}쪽` : '확인 중' }}</dd></div><div><dt>열람 가격</dt><dd>{{ report.price_krw ? `${Number(report.price_krw).toLocaleString('ko-KR')}원` : '구매 불가' }}</dd></div></dl>
      <p v-if="error" class="inline-error" role="alert">{{ error }}</p><p v-if="notice" class="inline-notice" role="status">{{ notice }}</p>
      <a v-if="report.access_url" class="solid-button" :href="report.access_url" target="_blank" rel="noopener noreferrer">공식 보고서 열기 ↗</a>
      <button v-else class="solid-button" type="button" :disabled="busy || !report.price_krw" @click="buy">{{ busy ? '결제 확인 중…' : report.price_krw ? '보고서 구매하기' : '검증된 페이지 수가 없어 구매할 수 없습니다' }}</button>
      <a class="report-source" :href="report.source_url" target="_blank" rel="noopener noreferrer">공식 출처 보기 ↗</a>
    </article>
    <p v-else-if="error" class="state-message error-state" role="alert">{{ error }}</p>
    <p v-else class="report-summary-card" aria-busy="true">보고서 정보를 불러오고 있습니다…</p>
  </main>
</template>
