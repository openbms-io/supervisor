import '@testing-library/jest-dom'
import fs from 'fs'
import path from 'path'

// Clean up test database before tests
beforeAll(() => {
  if (process.env.NODE_ENV !== 'test') {
    throw new Error('NODE_ENV is not test')
  }

  // Ensure Turso is not used in tests
  delete process.env.TURSO_DATABASE_URL
  delete process.env.TURSO_AUTH_TOKEN

  const testDbPath = path.join(process.cwd(), 'designer-test.db')
  const testDbWalPath = path.join(process.cwd(), 'designer-test.db-wal')
  const testDbShmPath = path.join(process.cwd(), 'designer-test.db-shm')

  // Remove existing test database files
  if (fs.existsSync(testDbPath)) {
    fs.unlinkSync(testDbPath)
  }
  if (fs.existsSync(testDbWalPath)) {
    fs.unlinkSync(testDbWalPath)
  }
  if (fs.existsSync(testDbShmPath)) {
    fs.unlinkSync(testDbShmPath)
  }
})

// Browser API mocks
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// localStorage mock
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Global fetch mock for libSQL client
global.Request = global.Request || class Request {}
global.Response = global.Response || class Response {}
global.fetch = global.fetch || jest.fn()
