module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/src/**/*.test.js'],
  transform: { '^.+\\.js$': 'babel-jest' },
  clearMocks: true,
}
