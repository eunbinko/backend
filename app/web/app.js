'use strict';
const $ = (selector) => document.querySelector(selector);
const defaultBase = '/api';
// 이전 버전의 백엔드 직접 연결 주소가 프록시 기본값을 덮어쓰지 않도록 분리합니다.
const storageKey = 'moa-api-base-proxy-v1';
function normalizeBase(value) {
  const input = value.trim();
  const relative = input.startsWith('/') && !input.startsWith('//');
  if (!relative && !/^https?:\/\//i.test(input)) {
    throw new Error('/api 같은 경로 또는 HTTP(S) 주소를 입력하세요.');
  }
  const url = new URL(input, location.origin);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || input.includes('\\')) {
    throw new Error('사용자 정보, 쿼리, 해시가 없는 API 주소를 입력하세요.');
  }
  return (relative ? url.pathname : url.href).replace(/\/+$/, '');
}
let apiBase = defaultBase;
try {
  const saved = localStorage.getItem(storageKey);
  if (saved) apiBase = normalizeBase(saved);
} catch {}
$('#api-base').value = apiBase;
let pending = 0;
function message(element, text, kind = '') {
  element.textContent = text;
  element.dataset.kind = kind;
}
function errorMessage(data, status) {
  if (Array.isArray(data?.detail)) {
    return data.detail.map(item => {
      const field = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : '';
      return (field ? field + ': ' : '') + (item.msg || '입력값을 확인하세요.');
    }).join('\n');
  }
  if (typeof data?.detail === 'string') return data.detail;
  if (status === 404) return '요청한 노트 또는 API를 찾을 수 없습니다.';
  if (status === 401 || status === 403) return '인증에 실패했습니다. 계정 정보를 확인하세요.';
  if (status >= 500) return '서버에서 처리하지 못했습니다. 입력 정보와 서버 로그를 확인하세요.';
  return '요청에 실패했습니다. (HTTP ' + status + ')';
}
async function request(path, payload) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(apiBase + path, {
      method: payload === undefined ? 'GET' : 'POST',
      credentials: 'include',
      headers: payload === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
      ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
      signal: controller.signal
    });
    const raw = await response.text();
    let data;
    try { data = raw ? JSON.parse(raw) : null; } catch {
      if (!response.ok) throw new Error(errorMessage(null, response.status));
      throw new Error('JSON 응답이 아닙니다. API 서버 주소를 확인하세요.');
    }
    if (!response.ok) throw new Error(errorMessage(data, response.status));
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('응답 시간이 초과되었습니다. 서버에서 이미 처리되었을 수 있으니 저장 요청을 반복하기 전에 확인하세요.');
    if (error instanceof TypeError) throw new Error('서버에 연결할 수 없습니다. 서버 실행 여부, API 주소 및 nginx 프록시 설정을 확인하세요.');
    throw error;
  } finally { clearTimeout(timer); }
}
async function run(form, action) {
  const button = form.querySelector('button[type="submit"]');
  if (button.disabled) return;
  const feedback = form.querySelector('.feedback');
  button.disabled = true;
  pending++;
  form.setAttribute('aria-busy', 'true');
  message(feedback, '처리 중입니다…');
  try { await action(feedback); }
  catch (error) { message(feedback, error.message, 'error'); }
  finally { button.disabled = false; pending--; form.removeAttribute('aria-busy'); }
}
function showAuth(mode) {
  for (const name of ['login', 'signup']) {
    $('#' + name + '-form').hidden = mode !== name;
    $('#' + name + '-tab').setAttribute('aria-pressed', String(mode === name));
  }
}
$('#login-tab').addEventListener('click', () => showAuth('login'));
$('#signup-tab').addEventListener('click', () => showAuth('signup'));
$('#settings-form').addEventListener('submit', event => {
  event.preventDefault();
  const output = $('#connection-status');
  if (pending) return message(output, '진행 중인 요청이 끝난 뒤 주소를 변경하세요.', 'error');
  try {
    apiBase = normalizeBase($('#api-base').value);
    $('#api-base').value = apiBase;
    try { localStorage.setItem(storageKey, apiBase); } catch {}
    $('#account').textContent = '오늘의 생각을 남겨보세요';
    $('#note-result').hidden = true;
    $('#empty-note').hidden = false;
    message(output, '서버 주소를 적용했습니다.', 'success');
  } catch (error) { message(output, error.message, 'error'); }
});
$('#check-server').addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  pending++;
  message($('#connection-status'), '적용된 서버에 연결 중입니다…');
  try {
    const data = await request('/');
    message($('#connection-status'), '연결되었습니다.' + (typeof data?.message === 'string' ? ' ' + data.message : ''), 'success');
  } catch (error) { message($('#connection-status'), error.message, 'error'); }
  finally { button.disabled = false; pending--; }
});
$('#signup-form').addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  run(form, async feedback => {
    const data = Object.fromEntries(new FormData(form));
    data.name = data.name.trim(); data.email = data.email.trim();
    if (!data.name) throw new Error('이름을 입력하세요.');
    const user = await request('/user/signup', data);
    if (typeof user?.email !== 'string' || typeof user?.name !== 'string') throw new Error('회원가입 응답 형식이 올바르지 않습니다.');
    form.reset();
    $('#login-email').value = user.email;
    message(feedback, user.name + '님, 가입되었습니다. 로그인 메뉴에서 로그인하세요.', 'success');
  });
});
$('#login-form').addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  run(form, async feedback => {
    const data = Object.fromEntries(new FormData(form));
    data.email = data.email.trim();
    const user = await request('/user/login', data);
    if (typeof user?.email !== 'string') throw new Error('로그인 응답을 확인할 수 없습니다.');
    $('#login-password').value = '';
    $('#account').textContent = user.email;
    message(feedback, '로그인 요청이 성공했습니다.', 'success');
  });
});
function showNote(note) {
  if (!Number.isSafeInteger(note?.idx) || typeof note.title !== 'string' || typeof note.contents !== 'string') {
    throw new Error('노트 응답 형식이 올바르지 않습니다. 서버에서 노트가 존재하는지 확인하세요.');
  }
  $('#result-id').textContent = 'NOTE ' + note.idx;
  $('#result-title').textContent = note.title;
  $('#result-contents').textContent = note.contents;
  $('#note-id').value = note.idx;
  $('#empty-note').hidden = true;
  $('#note-result').hidden = false;
}
$('#note-contents').addEventListener('input', event => {
  $('#character-count').textContent = event.target.value.length.toLocaleString('ko-KR') + '자';
});
$('#note-form').addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  run(form, async feedback => {
    const data = Object.fromEntries(new FormData(form));
    data.title = data.title.trim();
    if (!data.title || !data.contents.trim()) throw new Error('제목과 내용을 입력하세요.');
    const note = await request('/board/register', data);
    showNote(note);
    form.reset();
    $('#character-count').textContent = '0자';
    message(feedback, '저장되었습니다. 노트 번호: ' + note.idx + ' — 나중에 조회할 수 있도록 기억해 두세요.', 'success');
  });
});
$('#read-form').addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  run(form, async feedback => {
    $('#note-result').hidden = true;
    $('#empty-note').hidden = false;
    const id = Number($('#note-id').value);
    if (!Number.isSafeInteger(id)) throw new Error('노트 번호는 안전한 범위의 정수로 입력하세요.');
    showNote(await request('/board/read/' + encodeURIComponent(id)));
    message(feedback, '노트를 불러왔습니다.', 'success');
    $('#note-result').focus();
  });
});
