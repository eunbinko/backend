export function getInitialSelection(companies) {
  return companies[0]?.company_id || ''
}

export function selectCompany(companies, companyId) {
  return companies.some((company) => company.company_id === companyId)
    ? companyId
    : getInitialSelection(companies)
}

export function getThreadState(companies, selectedId) {
  return Object.fromEntries(companies.map(({ company_id }) => [company_id, company_id === selectedId]))
}

export function buildThreadPath(cardRect, markerRect, workspaceRect) {
  const fromX = Math.round(cardRect.left + cardRect.width / 2 - workspaceRect.left)
  const fromY = Math.round(cardRect.top + cardRect.height / 2 - workspaceRect.top)
  const toX = Math.round(markerRect.left + markerRect.width / 2 - workspaceRect.left)
  const toY = Math.round(markerRect.top + markerRect.height / 2 - workspaceRect.top)
  const distance = toX - fromX
  return `M ${fromX} ${fromY} C ${Math.round(fromX + distance * 0.27)} ${fromY}, ${Math.round(fromX + distance * 0.7)} ${toY}, ${toX} ${toY}`
}
