<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
const props = defineProps({ report: { type: Object, default: null }, company: { type: Object, default: null }, returnFocus: { type: Object, default: null } })
const emit = defineEmits(['close'])
const closeButton = ref(null)
function onKeydown(event) {
  if (event.key === 'Escape') emit('close')
  if (event.key === 'Tab' && props.report) {
    const focusable = document.querySelectorAll('.pdf-dialog button, .pdf-dialog a')
    if (!focusable.length) return
    const first = focusable[0]; const last = focusable[focusable.length - 1]
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }
}
watch(() => props.report, async (report) => {
  if (report) { document.body.classList.add('dialog-open'); await nextTick(); closeButton.value?.focus() }
  else { document.body.classList.remove('dialog-open'); props.returnFocus?.focus?.() }
})
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => { window.removeEventListener('keydown', onKeydown); document.body.classList.remove('dialog-open') })
</script>
<template>
  <Teleport to="body">
    <div v-if="report" class="pdf-backdrop" role="presentation" @click.self="emit('close')">
      <section class="pdf-dialog" role="dialog" aria-modal="true" :aria-labelledby="`pdf-title-${company?.company_id}`">
        <header class="pdf-dialog-header"><div><p class="section-kicker">공식 ESG 공시</p><h2 :id="`pdf-title-${company?.company_id}`">{{ company?.name }} · {{ report.title }}</h2></div><button ref="closeButton" class="dialog-close" type="button" aria-label="보고서 닫기" @click="emit('close')">×</button></header>
        <p class="pdf-source">원문 제공: {{ company?.name }} 공식 웹사이트</p>
        <iframe class="pdf-frame" :src="report.pdf_url" :title="`${company?.name} ${report.title} PDF 뷰어`" />
        <a class="official-link" :href="report.pdf_url" target="_blank" rel="noopener noreferrer">공식 PDF 새 탭에서 열기 ↗</a>
      </section>
    </div>
  </Teleport>
</template>
