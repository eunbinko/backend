export function getRoute(pathname) {
  const path = pathname.replace(/\/$/, '') || '/'
  if (path === '/signup') return { page: 'signup' }
  const report = path.match(/^\/reports\/(\d+)$/)
  if (report) return { page: 'report', id: Number(report[1]) }
  if (path === '/login') return { page: 'login', next: new URLSearchParams(window.location.search).get('next') }
  return { page: 'atlas' }
}

export function shouldLoadCurrentUser(page) { return page === 'report' || page === 'login' || page === 'signup' }
export function shouldShowAuthPage(page) { return page === 'login' || page === 'signup' }
