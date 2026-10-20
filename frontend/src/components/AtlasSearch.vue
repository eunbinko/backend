<script setup>
defineProps({ modelValue: { type: String, default: '' }, placeholder: { type: String, default: '기업명이나 공시 키워드 검색' } })
const emit = defineEmits(['update:modelValue', 'search'])
</script>

<template>
  <form class="atlas-search" role="search" @submit.prevent="emit('search', modelValue)">
    <label class="sr-only" for="atlas-search-input">기업 및 공시 검색</label>
    <span class="atlas-search__icon" aria-hidden="true">⌕</span>
    <input id="atlas-search-input" :value="modelValue" :placeholder="placeholder" @input="emit('update:modelValue', $event.target.value)" />
    <button type="submit">검색</button>
  </form>
</template>
