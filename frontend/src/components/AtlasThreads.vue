<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { buildThreadPath } from '../atlas-state'

const props = defineProps({ companies: { type: Array, default: () => [] }, selectedCompanyId: { type: String, default: '' } })
const threadPaths = ref([])
const svg = ref(null)
let workspace
let mutationObserver
let resizeObserver
let frame

function measureThreads() {
  if (!workspace || !svg.value) return
  const workspaceRect = workspace.getBoundingClientRect()
  svg.value.setAttribute('viewBox', `0 0 ${Math.round(workspaceRect.width)} ${Math.round(workspaceRect.height)}`)
  const cardElements = [...workspace.querySelectorAll('.cover-card[data-company-id]')]
  const markerElements = [...workspace.querySelectorAll('.leaflet-marker-icon[data-company-id]')]
  threadPaths.value = props.companies.flatMap((company) => {
    const card = cardElements.find((element) => element.dataset.companyId === company.company_id)
    const marker = markerElements.find((element) => element.dataset.companyId === company.company_id)
    if (!card || !marker) return []
    return [{
      id: company.company_id,
      active: company.company_id === props.selectedCompanyId,
      d: buildThreadPath(card.getBoundingClientRect(), marker.getBoundingClientRect(), workspaceRect),
    }]
  })
}

function scheduleMeasurement() {
  cancelAnimationFrame(frame)
  frame = requestAnimationFrame(measureThreads)
}

onMounted(async () => {
  await nextTick()
  workspace = svg.value?.closest('.atlas-workspace')
  if (!workspace) return
  mutationObserver = new MutationObserver(scheduleMeasurement)
  mutationObserver.observe(workspace, { childList: true, subtree: true })
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(scheduleMeasurement)
    resizeObserver.observe(workspace)
  }
  window.addEventListener('resize', scheduleMeasurement)
  scheduleMeasurement()
})
watch(() => [props.companies, props.selectedCompanyId], async () => { await nextTick(); scheduleMeasurement() }, { deep: true })
onUnmounted(() => {
  cancelAnimationFrame(frame)
  mutationObserver?.disconnect()
  resizeObserver?.disconnect()
  window.removeEventListener('resize', scheduleMeasurement)
})
</script>

<template>
  <svg ref="svg" class="atlas-threads" preserveAspectRatio="none" aria-hidden="true">
    <path v-for="path in threadPaths" :key="path.id" :d="path.d" :class="{ 'is-active': path.active }" />
  </svg>
</template>
