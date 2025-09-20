/** @jest-environment node */

import { projectsRepository } from './projects'
import { closeDatabase, getDatabase } from './client'
import { projects as projectsTable } from './schema'

describe('ProjectsRepository (SQLite + Drizzle)', () => {
  beforeEach(async () => {
    // Clean projects table before each test
    const db = getDatabase()
    await db.delete(projectsTable).run()
  })
  afterAll(() => {
    // Close DB handle to avoid file locks between test runs
    closeDatabase()
  })

  function expectIsoString(value: unknown): asserts value is string {
    expect(typeof value).toBe('string')
    // Basic ISO-8601 shape check
    expect(() => new Date(value as string)).not.toThrow()
  }

  it('creates and reads back a project with workflow_config', async () => {
    const created = await projectsRepository.create({
      name: 'Repo Test Alpha',
      description: 'Created via repository test',
      workflow_config: { foo: 'bar' },
    })

    expect(created.id).toMatch(/[0-9a-fA-F-]{36}/)
    expect(created.name).toBe('Repo Test Alpha')
    expect(created.description).toBe('Created via repository test')
    expect(typeof created.workflow_config).toBe('string')
    expect(created.workflow_config).toBe(JSON.stringify({ foo: 'bar' }))
    expectIsoString(created.created_at)
    expectIsoString(created.updated_at)

    const fetched = await projectsRepository.findById(created.id)
    expect(fetched).not.toBeNull()
    expect(fetched!.id).toBe(created.id)
    expect(fetched!.name).toBe(created.name)
    expect(fetched!.description).toBe(created.description)
    expect(fetched!.workflow_config).toBe(JSON.stringify({ foo: 'bar' }))
  })

  it('creates with minimal fields and default workflow_config', async () => {
    const created = await projectsRepository.create({
      name: 'Repo Test Minimal',
      workflow_config: {},
    })

    expect(created.name).toBe('Repo Test Minimal')
    expect(created.description).toBeUndefined()
    expect(created.workflow_config).toBe(JSON.stringify({}))

    const again = await projectsRepository.findById(created.id)
    expect(again!.workflow_config).toBe('{}')
  })

  it('updates name, clears description, and replaces workflow_config', async () => {
    const created = await projectsRepository.create({
      name: 'Repo Test Update',
      description: 'desc',
      workflow_config: { a: 1 },
    })

    // Ensure updated_at will differ from created.updated_at
    await new Promise((r) => setTimeout(r, 5))

    const updated = await projectsRepository.update(created.id, {
      name: 'Repo Test Updated',
      // empty string coerces to null in repository
      description: '',
      workflow_config: { b: 2 },
    })

    expect(updated).not.toBeNull()
    expect(updated!.id).toBe(created.id)
    expect(updated!.name).toBe('Repo Test Updated')
    expect(updated!.description).toBeUndefined()
    expect(updated!.workflow_config).toBe(JSON.stringify({ b: 2 }))
    // updated_at should be greater than created.updated_at
    expect(new Date(updated!.updated_at).getTime()).toBeGreaterThan(
      new Date(created.updated_at).getTime()
    )
  })

  it('exists(), count(), delete(), and findById() behave as expected', async () => {
    const beforeCount = await projectsRepository.count()

    const p = await projectsRepository.create({
      name: 'Repo Test Delete',
      workflow_config: {},
    })
    const q = await projectsRepository.create({
      name: 'Repo Test Delete 2',
      workflow_config: null as unknown as object,
    })

    const midCount = await projectsRepository.count()
    expect(midCount).toBe(beforeCount + 2)

    expect(await projectsRepository.exists(p.id)).toBe(true)
    expect(
      await projectsRepository.exists('00000000-0000-0000-0000-000000000000')
    ).toBe(false)

    const deleted = await projectsRepository.delete(p.id)
    expect(deleted).toBe(true)
    expect(await projectsRepository.findById(p.id)).toBeNull()
    expect(await projectsRepository.exists(p.id)).toBe(false)

    const deletedAgain = await projectsRepository.delete(p.id)
    expect(deletedAgain).toBe(false)

    const afterCount = await projectsRepository.count()
    expect(afterCount).toBe(beforeCount + 1) // one remains (q)
    // Cleanup remaining test project
    await projectsRepository.delete(q.id)
  })

  it('list() with search/sort and searchByName() return expected projects', async () => {
    const a = await projectsRepository.create({
      name: 'Zeta Project A',
      workflow_config: {},
    })
    const b = await projectsRepository.create({
      name: 'Zeta Project B',
      workflow_config: {},
    })

    const listByNameAsc = await projectsRepository.list({
      search: 'Zeta Project',
      sort: 'name',
      order: 'asc',
      page: 1,
      limit: 50,
    })

    const zetas = listByNameAsc.projects.filter((p) =>
      p.name.startsWith('Zeta Project')
    )
    const names = zetas.map((p) => p.name)
    expect(names).toEqual(['Zeta Project A', 'Zeta Project B'])

    const searchByName = await projectsRepository.searchByName('Zeta Project')
    const searchNames = searchByName.map((p) => p.name).sort()
    expect(searchNames).toEqual(['Zeta Project A', 'Zeta Project B'])

    // Cleanup
    await projectsRepository.delete(a.id)
    await projectsRepository.delete(b.id)
  })
})
