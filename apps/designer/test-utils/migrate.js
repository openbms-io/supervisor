import path from 'path'
import Database from 'better-sqlite3'
import { drizzle } from 'drizzle-orm/better-sqlite3'
import { migrate } from 'drizzle-orm/better-sqlite3/migrator'

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

export function migrateTestDatabase() {
  const dbPath = getDbPath()
  const sqlite = new Database(dbPath)
  configureSqlite(sqlite)

  const db = drizzle(sqlite)
  const migrationsFolder = path.join(process.cwd(), 'src/lib/db/migrations')
  migrate(db, { migrationsFolder })

  try {
    sqlite.close()
  } catch {}
}
