export function getRoute(pathname) {
  const path = pathname.replace(/\/$/, '') || '/'
  if (path === '/login') return { page: 'login' }
  if (path === '/signup') return { page: 'signup' }
  if (path === '/write') return { page: 'write' }
  const detail = path.match(/^\/posts\/(\d+)$/)
  if (detail) return { page: 'detail', id: Number(detail[1]) }
  return { page: 'atlas' }
}

export function shouldLoadBoardList(page) { return page === 'list' }
export function shouldLoadCurrentUser(page) { return page !== 'atlas' }
