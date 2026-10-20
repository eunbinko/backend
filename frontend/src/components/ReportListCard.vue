<script setup>
defineProps({
  report: { type: Object, required: true },
  active: { type: Boolean, default: false },
})
const emit = defineEmits(['select'])
</script>

<template>
  <button class="atlas-report-card" :class="{ 'is-active': active }" type="button" :aria-pressed="active" @click="emit('select', report)">
    <span class="atlas-report-card__eyebrow">{{ report.company_name }} · {{ report.report_year }}</span>
    <strong>{{ report.title }}</strong>
    <span class="atlas-report-card__summary">{{ report.summary }}</span>
    <span class="atlas-report-card__meta"><slot name="meta">공시 보고서</slot><span aria-hidden="true">↗</span></span>
  </button>
</template>
