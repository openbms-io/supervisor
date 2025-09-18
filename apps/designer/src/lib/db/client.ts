import 'server-only'

import Database from 'better-sqlite3'
import {
  drizzle as drizzleBetter,
  BetterSQLite3Database,
} from 'drizzle-orm/better-sqlite3'
import { migrate } from 'drizzle-orm/better-sqlite3/migrator'
import { createClient as createLibsql } from '@libsql/client'
import {
  drizzle as drizzleLibsql,
  type LibSQLDatabase,
} from 'drizzle-orm/libsql'
import { join } from 'path'
import * as schema from './schema'

let db:
  | (BetterSQLite3Database<typeof schema> | LibSQLDatabase<typeof schema>)
  | null = null
let sqlite: Database.Database | null = null

const useTurso = Boolean(process.env.TURSO_DATABASE_URL)

export function getDatabase():
  | BetterSQLite3Database<typeof schema>
  | LibSQLDatabase<typeof schema> {
  // Ensure we're running on the server
  if (typeof window !== 'undefined') {
    throw new Error('Database operations can only be performed on the server')
  }

  if (!db) {
    if (useTurso) {
      // Remote (Turso/libSQL) client
      const client = createLibsql({
        url: process.env.TURSO_DATABASE_URL!,
        authToken: process.env.TURSO_AUTH_TOKEN,
      })
      db = drizzleLibsql(client, { schema })
      // Do not run migrations at runtime on Turso/serverless
      console.log('Drizzle (libsql) initialized for Turso')
    } else {
      // Local file-based SQLite for dev
      const dbPath = process.env.DATABASE_PATH
        ? join(process.cwd(), process.env.DATABASE_PATH)
        : join(process.cwd(), 'designer.db')
      sqlite = new Database(dbPath)

      // Enable WAL mode for better concurrency
      sqlite.exec('PRAGMA journal_mode = WAL')
      sqlite.exec('PRAGMA synchronous = NORMAL')
      sqlite.exec('PRAGMA cache_size = 1000')
      sqlite.exec('PRAGMA foreign_keys = ON')

      // Basic pragmas for local dev; avoid WAL to keep it simple
      sqlite.exec('PRAGMA foreign_keys = ON')

      db = drizzleBetter(sqlite, { schema })

      // Run migrations locally
      const migrationsFolder = join(process.cwd(), 'src/lib/db/migrations')
      migrate(db, { migrationsFolder })
      console.log(`Drizzle (better-sqlite3) initialized at ${dbPath}`)
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
