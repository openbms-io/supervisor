/** @jest-environment node */

import { randomUUID } from 'crypto'

import { getDatabase, closeDatabase } from './client'
import { projects } from './schema'
import { eq } from 'drizzle-orm'

describe('Database Client (SQLite + Drizzle)', () => {
  afterAll(() => {
    // Ensure DB connection is closed and file handles released
    closeDatabase()
  })

  it('loads .env.test and uses test database path', () => {
    expect(process.env.NODE_ENV).toBe('test')
    expect(process.env.DATABASE_PATH).toBe('designer-test.db')
  })

  it('initializes database and runs migrations (projects table exists)', async () => {
    const db = getDatabase()

    // Selecting from the projects table should not throw if migrations ran
    const rows = await db.select().from(projects).limit(1).all()
    expect(Array.isArray(rows)).toBe(true)
  })

  it('projects table can be queried (no seed assumption)', async () => {
    const db = getDatabase()

    const all = await db.select().from(projects).all()
    expect(Array.isArray(all)).toBe(true)
    // If any rows exist, basic shape sanity
    for (const p of all) {
      expect(typeof p.id).toBe('string')
      expect(typeof p.name).toBe('string')
    }
  })

  it('supports insert and readback for projects', async () => {
    const db = getDatabase()

    const id = randomUUID()
    const name = 'Test Project'

    // Insert minimal row (defaults for workflow_config/created_at/updated_at)
    await db.insert(projects).values({ id, name }).run()

    const fetched = await db
      .select()
      .from(projects)
      .where(eq(projects.id, id))
      .get()

    expect(fetched).toBeTruthy()
    expect(fetched?.id).toBe(id)
    expect(fetched?.name).toBe(name)
    // Defaults are applied
    expect(typeof fetched?.created_at).toBe('string')
    expect(typeof fetched?.updated_at).toBe('string')
    expect(typeof fetched?.workflow_config).toBe('string')
  })
})
