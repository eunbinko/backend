export function getRoute(pathname) {
  const path = pathname.replace(/\/$/, '') || '/'
  if (path === '/signup') return { page: 'signup' }
  if (path === '/write') return { page: 'write' }
  const report = path.match(/^\/reports\/(\d+)$/)
  if (report) return { page: 'report', id: Number(report[1]) }
  if (path === '/login') return { page: 'login', next: new URLSearchParams(window.location.search).get('next') }
  const detail = path.match(/^\/posts\/(\d+)$/)
  if (detail) return { page: 'detail', id: Number(detail[1]) }
  return { page: 'atlas' }
}

export function shouldLoadBoardList(page) { return page === 'list' }
export function shouldLoadCurrentUser(page) { return page !== 'atlas' }
