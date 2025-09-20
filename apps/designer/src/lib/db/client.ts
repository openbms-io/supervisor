import 'server-only'

import Database from 'better-sqlite3'
import {
  drizzle as drizzleBetter,
  BetterSQLite3Database,
} from 'drizzle-orm/better-sqlite3'
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

function assertServer(): void {
  if (typeof window !== 'undefined') {
    throw new Error('Database operations can only be performed on the server')
  }
}

function getDbPath(): string {
  return process.env.DATABASE_PATH
    ? join(process.cwd(), process.env.DATABASE_PATH)
    : join(process.cwd(), 'designer.db')
}

function configureSqlitePragmas(db: Database.Database): void {
  try {
    db.exec('PRAGMA journal_mode = WAL')
    db.exec('PRAGMA synchronous = NORMAL')
    db.exec('PRAGMA cache_size = 1000')
  } catch {
    // Ignore pragma errors (some platforms may not support them)
    console.warn('Failed to set sqlite pragmas')
  }
  try {
    db.exec('PRAGMA foreign_keys = ON')
  } catch {
    console.warn('Failed to set sqlite foreign keys')
  }
}

function initSqlite(): BetterSQLite3Database<typeof schema> {
  const dbPath = getDbPath()
  sqlite = new Database(dbPath)
  configureSqlitePragmas(sqlite)
  const better = drizzleBetter(sqlite, { schema })
  console.log(`Drizzle (better-sqlite3) initialized at ${dbPath}`)
  return better
}

function initLibsql(): LibSQLDatabase<typeof schema> {
  const client = createLibsql({
    url: process.env.TURSO_DATABASE_URL!,
    authToken: process.env.TURSO_AUTH_TOKEN,
  })
  const libsql = drizzleLibsql(client, { schema })
  console.log('Drizzle (libsql) initialized for Turso')
  return libsql
}

export function getDatabase():
  | BetterSQLite3Database<typeof schema>
  | LibSQLDatabase<typeof schema> {
  assertServer()
  if (!db) {
    db = useTurso ? initLibsql() : initSqlite()
  }
  return db!
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
