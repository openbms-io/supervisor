import '@testing-library/jest-dom'
import fs from 'fs'
import path from 'path'
import { migrateTestDatabase } from './test-utils/migrate'
// Mock ESM-only uuid globally so Jest (CJS) doesn't choke on export syntax
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
  v5: jest.fn(() => 'mock-uuid-v5'),
}))

// Clean up test database before tests
beforeAll(async () => {
  if (process.env.NODE_ENV !== 'test') {
    throw new Error('NODE_ENV is not test')
  }

  // Ensure Turso is not used in tests
  delete process.env.TURSO_DATABASE_URL
  delete process.env.TURSO_AUTH_TOKEN

  console.log('process.env.DATABASE_PATH', process.env.DATABASE_PATH)
  const testDbPath = path.join(process.cwd(), process.env.DATABASE_PATH)
  const testDbWalPath = `${testDbPath}-wal`
  const testDbShmPath = `${testDbPath}-shm`

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

  // Run DB migrations for the test database
  migrateTestDatabase()
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
