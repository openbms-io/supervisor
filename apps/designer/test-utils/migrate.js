const path = require('path')
const Database = require('better-sqlite3')
const { drizzle } = require('drizzle-orm/better-sqlite3')
const { migrate } = require('drizzle-orm/better-sqlite3/migrator')

function configureSqlite(db) {
  try {
    db.exec('PRAGMA journal_mode = WAL')
  } catch {}
  try {
    db.exec('PRAGMA synchronous = NORMAL')
  } catch {}
  try {
    db.exec('PRAGMA cache_size = 1000')
  } catch {}
  try {
    db.exec('PRAGMA busy_timeout = 2000')
  } catch {}
  try {
    db.exec('PRAGMA foreign_keys = ON')
  } catch {}
}

function getDbPath() {
  const file = process.env.DATABASE_PATH || 'designer-test.db'
  return path.join(process.cwd(), file)
}

function migrateTestDatabase() {
  const dbPath = getDbPath()
  const sqlite = new Database(dbPath)
  configureSqlite(sqlite)

  // Create a drizzle instance (schema typing not needed for migrations)
  const db = drizzle(sqlite)

  // Run migrations synchronously
  const migrationsFolder = path.join(process.cwd(), 'src/lib/db/migrations')
  migrate(db, { migrationsFolder })

  // Close sqlite handle
  try {
    sqlite.close()
  } catch {}
}

module.exports = { migrateTestDatabase }
