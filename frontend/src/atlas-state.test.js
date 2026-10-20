import { getInitialSelection, selectCompany, getThreadState, buildThreadPath } from './atlas-state'

describe('atlas selection state', () => {
  const companies = [{ company_id: 'alpha' }, { company_id: 'beta' }]

  test('selects the first company when data arrives', () => {
    expect(getInitialSelection(companies)).toBe('alpha')
  })

  test('updates selection only to an available company', () => {
    expect(selectCompany(companies, 'beta')).toBe('beta')
    expect(selectCompany(companies, 'missing')).toBe('alpha')
  })

  test('marks exactly the selected company thread active', () => {
    expect(getThreadState(companies, 'beta')).toEqual({ alpha: false, beta: true })
  })

  test('connects measured cover and marker centers in workspace coordinates', () => {
    expect(buildThreadPath({ left: 10, top: 20, width: 40, height: 60 }, { left: 310, top: 220, width: 20, height: 20 }, { left: 0, top: 0 }))
      .toBe('M 30 50 C 108 50, 233 230, 320 230')
  })
})
