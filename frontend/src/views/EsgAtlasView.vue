<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchEsgCompanies } from '../api/esg'
import { getInitialSelection, selectCompany } from '../atlas-state'
import AtlasThreads from '../components/AtlasThreads.vue'
import KoreaCompanyMap from '../components/KoreaCompanyMap.vue'
import ReportCoverRail from '../components/ReportCoverRail.vue'
import AtlasSearch from '../components/AtlasSearch.vue'
import ReportListCard from '../components/ReportListCard.vue'

const companies = ref([])
const fiscalYear = ref(2025)
const revenueBasis = ref('standalone')
const rankingSource = ref('')
const selectedCompanyId = ref('')
const loading = ref(true)
const error = ref('')
const activeReport = ref(null)
const returnFocus = ref(null)
const selectedCompany = computed(() => companies.value.find(({ company_id }) => company_id === selectedCompanyId.value) || null)
const selectedReport = computed(() => activeReport.value?.report || null)
const reportCompany = computed(() => activeReport.value?.company || null)
const searchQuery = ref('')

async function loadCompanies() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchEsgCompanies({ fiscalYear: 2025 })
    companies.value = data.companies
    fiscalYear.value = data.fiscal_year
    revenueBasis.value = data.revenue_basis
    rankingSource.value = data.ranking_source_url
    selectedCompanyId.value = selectCompany(companies.value, selectedCompanyId.value) || getInitialSelection(companies.value)
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
}
function openReport({ report }) { window.history.pushState({}, '', `/reports/${report.id}`); window.dispatchEvent(new PopStateEvent('popstate')) }
function searchCompanies(query) {
  searchQuery.value = query.trim()
  if (!searchQuery.value) return
  const match = companies.value.find((company) => `${company.name} ${company.industry} ${company.esg_highlights}`.toLowerCase().includes(searchQuery.value.toLowerCase()))
  if (match) selectedCompanyId.value = match.company_id
}
function openCompanyReport(report) { if (report.id) openReport({ report }) }
onMounted(loadCompanies)
</script>

<template>
  <main id="main" class="atlas-page">
    <header class="atlas-masthead">
      <a class="atlas-brand" href="/" aria-label="공시 아틀라스 홈"><span class="atlas-brand-mark" aria-hidden="true">A</span><b>공시 아틀라스</b><span>대한민국 ESG 보고서 지도</span></a>
      <div class="atlas-edition">{{ fiscalYear }} 회계연도 <span>·</span> 별도 기준 매출 상위 10개사</div>
      <a class="atlas-account" href="/login">로그인 <span aria-hidden="true">↗</span></a>
    </header>
    <section class="atlas-intro" aria-labelledby="atlas-title">
      <div><p class="atlas-kicker">매출로 찾는 지속가능성 공시</p><h1 id="atlas-title">기업의 위치에서<br />공시의 맥락으로.</h1><p class="atlas-lede">대한민국 주요 기업의 본사와 ESG 보고서를 한 장의 지도로 잇습니다.</p></div>
      <AtlasSearch v-model="searchQuery" @search="searchCompanies" />
      <div class="atlas-count"><strong>{{ String(companies.length).padStart(2, '0') }}</strong><span>기업 기록</span></div>
    </section>
    <div v-if="loading" class="atlas-state" role="status" aria-live="polite">2025년 기업 공시 자료를 불러오고 있습니다…</div>
    <div v-else-if="error" class="atlas-state atlas-error" role="alert"><strong>공시 자료를 불러오지 못했습니다.</strong><span>{{ error }}</span><button type="button" @click="loadCompanies">다시 시도</button></div>
    <div v-else-if="!companies.length" class="atlas-state" role="status">표시할 기업 자료가 없습니다.</div>
    <template v-else>
      <section class="atlas-workspace" aria-label="기업 위치와 보고서 탐색">
        <ReportCoverRail class="rail-left" :companies="companies.slice(0, 5)" :selected-company-id="selectedCompanyId" @select="selectedCompanyId = $event" @open-report="openReport" />
        <div class="map-stage">
          <div class="map-caption"><span>대한민국</span><span>본사 위치 · {{ companies.length }}곳</span></div>
          <KoreaCompanyMap :companies="companies" :selected-company-id="selectedCompanyId" @select="selectedCompanyId = $event" />
          <AtlasThreads :companies="companies" :selected-company-id="selectedCompanyId" />
          <div class="map-legend"><i></i> 선택한 기업</div>
        </div>
        <ReportCoverRail class="rail-right" :companies="companies.slice(5)" :selected-company-id="selectedCompanyId" @select="selectedCompanyId = $event" @open-report="openReport" />
      </section>
      <section v-if="selectedCompany" class="company-detail" aria-live="polite" :aria-labelledby="`company-${selectedCompany.company_id}`">
        <div class="detail-rank"><span>{{ selectedCompany.rank }}위</span><strong>{{ Number(selectedCompany.revenue_krw).toLocaleString('ko-KR') }}</strong><small>원 · {{ fiscalYear }} 별도 매출</small></div>
        <div class="detail-main"><p class="atlas-kicker">{{ selectedCompany.industry }} <span>·</span> {{ selectedCompany.headquarters?.label }}</p><h2 :id="`company-${selectedCompany.company_id}`">{{ selectedCompany.name }}</h2><p>{{ selectedCompany.esg_highlights }}</p><a v-if="selectedCompany.sources?.esg_highlights" :href="selectedCompany.sources.esg_highlights" target="_blank" rel="noopener noreferrer">하이라이트 출처 ↗</a></div>
        <a v-if="rankingSource" class="ranking-source" :href="rankingSource" target="_blank" rel="noopener noreferrer">순위 출처 ↗</a>
      </section>
    </template>
    <section v-if="selectedCompany?.reports?.length" class="related-reports" aria-label="선택 기업의 ESG 공시 보고서">
      <div class="related-reports__heading"><p class="atlas-kicker">공식 보고서</p><h2>{{ selectedCompany.name }}의 공시</h2></div>
      <div class="related-reports__list"><ReportListCard v-for="report in selectedCompany.reports" :key="report.id || report.source_url" :report="{ ...report, company_name: selectedCompany.name }" @select="openCompanyReport"><template #meta>{{ report.page_count ? `${report.page_count}쪽` : '요약 보기' }}</template></ReportListCard></div>
    </section>
    <footer class="atlas-footer"><span>공시 아틀라스</span><span>공시 자료는 각 기업의 공식 출처를 따릅니다.</span></footer>
  </main>
</template>
