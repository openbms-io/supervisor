// Load test environment variables
// Note: Next.js automatically loads .env.test in test environment

// Ensure critical test environment variables are set
if (process.env.NODE_ENV !== 'test') {
  process.env.NODE_ENV = 'test'
}

// Ensure Turso is not used in tests
delete process.env.TURSO_DATABASE_URL
delete process.env.TURSO_AUTH_TOKEN
