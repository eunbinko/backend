<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({ companies: { type: Array, default: () => [] }, selectedCompanyId: { type: String, default: '' } })
const emit = defineEmits(['select'])
const mapElement = ref(null)
let map
let markerLayer

function renderMarkers() {
  if (!map || !markerLayer) return
  markerLayer.clearLayers()
  props.companies.forEach((company) => {
    const { latitude, longitude } = company.headquarters || {}
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return
    const selected = company.company_id === props.selectedCompanyId
    const marker = L.marker([latitude, longitude], {
      icon: L.divIcon({ className: `atlas-marker${selected ? ' is-selected' : ''}`, html: `<span aria-hidden="true">${company.rank}</span>`, iconSize: [32, 32], iconAnchor: [16, 16] }),
      title: `${company.rank}위 ${company.name} 본사`,
      keyboard: true,
    })
    marker.getElement()?.setAttribute('data-company-id', company.company_id)
    marker.on('click keypress', () => emit('select', company.company_id))
    marker.addTo(markerLayer)
  })
}

onMounted(() => {
  map = L.map(mapElement.value, { scrollWheelZoom: false, zoomControl: true, minZoom: 6 }).setView([36.4, 127.8], 7)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)
  markerLayer = L.layerGroup().addTo(map)
  renderMarkers()
})
watch(() => [props.companies, props.selectedCompanyId], renderMarkers, { deep: true })
onUnmounted(() => { if (map) map.remove() })
</script>

<template>
  <div ref="mapElement" class="korea-map" role="region" aria-label="대한민국 기업 본사 위치 지도">
    <p class="map-loading">지도를 불러오는 중입니다.</p>
  </div>
</template>
