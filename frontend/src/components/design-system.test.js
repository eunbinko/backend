const fs = require('fs')
const path = require('path')
const { parse, compileTemplate } = require('@vue/compiler-sfc')

const componentNames = ['AtlasSearch.vue', 'ReportListCard.vue', 'AuthPanel.vue']

describe('reusable atlas interface components', () => {
  test.each(componentNames)('%s has a valid Vue template and semantic controls', (name) => {
    const filename = path.join(__dirname, name)
    const source = fs.readFileSync(filename, 'utf8')
    const { descriptor, errors } = parse(source, { filename })

    expect(errors).toEqual([])
    expect(descriptor.template).not.toBeNull()
    expect(compileTemplate({ source: descriptor.template.content, filename, id: name }).errors).toEqual([])
    expect(source).toContain('<script setup>')
  })

  test('authentication form exposes labels and supports login and signup modes', () => {
    const source = fs.readFileSync(path.join(__dirname, 'AuthPanel.vue'), 'utf8')

    expect(source).toContain('mode === \'signup\'')
    expect(source).toContain('for="account-email"')
    expect(source).toContain('for="account-password"')
    expect(source).toContain('emit(\'submit\')')
  })
})
