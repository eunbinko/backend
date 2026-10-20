<script setup>
import { ref, watch } from 'vue'
import { getOfficialReportUrl, hasOfficialPdf } from '../report-links'

const props = defineProps({ companies: { type: Array, default: () => [] }, selectedCompanyId: { type: String, default: '' } })
const emit = defineEmits(['select', 'open-report'])
const failedImages = ref(new Set())
watch(() => props.companies, () => { failedImages.value = new Set() })
function imageFailed(report, companyId) { failedImages.value = new Set([...failedImages.value, report.source_url || companyId]) }
</script>

<template>
  <section class="cover-rail" aria-label="ESG 공시 보고서 표지">
    <h2 class="rail-heading">보고서</h2>
    <article v-for="company in companies" :key="company.company_id" class="cover-card" :data-company-id="company.company_id" :class="{ 'is-selected': selectedCompanyId === company.company_id }">
      <button class="cover-select" type="button" :aria-pressed="selectedCompanyId === company.company_id" :aria-label="`${company.rank}위 ${company.name} 선택`" @click="emit('select', company.company_id)">
        <img v-if="company.reports?.[0]?.cover_image_url && !failedImages.has(company.reports[0].source_url || company.company_id)" :src="company.reports[0].cover_image_url" :alt="`${company.name} ${company.reports[0].report_year}년 보고서 표지`" loading="lazy" @error="imageFailed(company.reports[0], company.company_id)" />
        <span v-else class="cover-placeholder" aria-hidden="true"><span>{{ company.reports?.[0]?.report_year || 'ESG' }}</span><strong>{{ company.name }}</strong><small>공식 보고서</small></span>
        <span class="cover-company"><b>{{ String(company.rank).padStart(2, '0') }}</b>{{ company.name }}</span>
      </button>
      <a v-if="company.reports?.[0] && (!company.reports[0].cover_image_url || failedImages.has(company.reports[0].source_url || company.company_id))" class="report-open" :href="company.reports[0].landing_page_url || company.reports[0].source_url" target="_blank" rel="noopener noreferrer">공식 표지 출처 ↗</a>
      <button v-if="company.reports?.[0]" class="report-open" type="button" :disabled="!company.reports[0].id" @click="emit('open-report', { company, report: company.reports[0], event: $event })">보고서 상세 보기 <span aria-hidden="true">↗</span></button>
      <a v-else-if="getOfficialReportUrl(company.reports?.[0])" class="report-open" :href="getOfficialReportUrl(company.reports?.[0])" target="_blank" rel="noopener noreferrer">공식 보고서 보기 ↗</a>
      <a v-else class="report-open" :href="company.sources?.esg_highlights" target="_blank" rel="noreferrer">출처 보기 ↗</a>
    </article>
  </section>
</template>
