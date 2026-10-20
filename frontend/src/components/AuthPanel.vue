<script setup>
defineProps({
  mode: { type: String, default: 'login' },
  model: { type: Object, required: true },
  busy: { type: Boolean, default: false },
  error: { type: String, default: '' },
  notice: { type: String, default: '' },
})
const emit = defineEmits(['submit', 'navigate'])
</script>

<template>
  <section class="atlas-auth-card" :aria-labelledby="mode === 'signup' ? 'signup-title' : 'login-title'">
    <a class="atlas-auth-brand" href="/" @click.prevent="emit('navigate', '/')"><span class="atlas-brand-mark" aria-hidden="true">A</span><span>공시 아틀라스</span></a>
    <p class="atlas-auth-kicker">기업 공시를 한눈에</p>
    <h1 :id="mode === 'signup' ? 'signup-title' : 'login-title'">{{ mode === 'signup' ? '아틀라스 시작하기' : '다시 만나 반가워요' }}</h1>
    <p class="atlas-auth-description">{{ mode === 'signup' ? '계정을 만들고 공시 탐색을 시작하세요.' : '로그인하고 보고서 구매 내역을 확인하세요.' }}</p>
    <form class="atlas-auth-form" @submit.prevent="emit('submit')">
      <label v-if="mode === 'signup'" for="account-name">이름</label>
      <input v-if="mode === 'signup'" id="account-name" v-model="model.name" name="name" autocomplete="name" required placeholder="이름을 입력하세요" />
      <label for="account-email">이메일</label>
      <input id="account-email" v-model="model.email" name="email" type="email" autocomplete="username" spellcheck="false" required placeholder="name@example.com" />
      <label for="account-password">비밀번호</label>
      <input id="account-password" v-model="model.password" name="password" type="password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" minlength="1" maxlength="128" required placeholder="비밀번호를 입력하세요" />
      <p v-if="error" class="inline-error" role="alert">{{ error }}</p>
      <p v-if="notice" class="inline-notice" role="status">{{ notice }}</p>
      <button class="atlas-auth-submit" type="submit" :disabled="busy">{{ busy ? '처리 중…' : mode === 'signup' ? '회원가입' : '로그인' }}</button>
    </form>
    <p class="atlas-auth-switch">{{ mode === 'signup' ? '이미 계정이 있나요?' : '아직 계정이 없나요?' }} <a :href="mode === 'signup' ? '/login' : '/signup'" @click.prevent="emit('navigate', mode === 'signup' ? '/login' : '/signup')">{{ mode === 'signup' ? '로그인' : '회원가입' }}</a></p>
    <div class="atlas-auth-social"><span>또는</span><slot name="social" /></div>
  </section>
</template>
