module.exports = {
  testEnvironment: 'jsdom',
  testRegex: '/src/.*\\.test\\.js$',
  transform: { '^.+\\.js$': 'babel-jest' },
  clearMocks: true,
}
