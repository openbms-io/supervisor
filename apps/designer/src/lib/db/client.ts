import 'server-only'

import Database from 'better-sqlite3'
import { drizzle, BetterSQLite3Database } from 'drizzle-orm/better-sqlite3'
import { migrate } from 'drizzle-orm/better-sqlite3/migrator'
import { join } from 'path'
import * as schema from './schema'

let db: BetterSQLite3Database<typeof schema> | null = null
let sqlite: Database.Database | null = null

export function getDatabase(): BetterSQLite3Database<typeof schema> {
  // Ensure we're running on the server
  if (typeof window !== 'undefined') {
    throw new Error('Database operations can only be performed on the server')
  }

  if (!db) {
    const dbPath = join(process.cwd(), 'designer.db')

    // Create SQLite connection
    sqlite = new Database(dbPath)

    // Enable WAL mode for better concurrency
    sqlite.exec('PRAGMA journal_mode = WAL')
    sqlite.exec('PRAGMA synchronous = NORMAL')
    sqlite.exec('PRAGMA cache_size = 1000')
    sqlite.exec('PRAGMA foreign_keys = ON')

    // Create Drizzle database instance
    db = drizzle(sqlite, { schema })

    // Run migrations only on server
    if (process.env.NODE_ENV !== 'test') {
      const migrationsFolder = join(process.cwd(), 'src/lib/db/migrations')
      migrate(db, { migrationsFolder })
      console.log(`Drizzle database initialized at ${dbPath}`)
    }
  }

  return db
}

export function closeDatabase(): void {
  if (sqlite) {
    sqlite.close()
    sqlite = null
    db = null
  }
}

// Gracefully close database on process exit
if (typeof process !== 'undefined') {
  process.on('exit', closeDatabase)
  process.on('SIGINT', closeDatabase)
  process.on('SIGTERM', closeDatabase)
}
