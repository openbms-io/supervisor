/** @jest-environment node */

import { deploymentConfigRepository } from './deployment-config'
import { closeDatabase, getDatabase } from './client'
import { deploymentConfig as deploymentConfigTable } from './schema'

describe('DeploymentConfigRepository (SQLite + Drizzle)', () => {
  beforeEach(async () => {
    const db = getDatabase()
    await db.delete(deploymentConfigTable).run()
  })
  afterAll(() => {
    closeDatabase()
  })

  function expectIsoString(value: unknown): asserts value is string {
    expect(typeof value).toBe('string')
    expect(() => new Date(value as string)).not.toThrow()
  }

  it('creates default config when none exists via getOrCreate', async () => {
    const config = await deploymentConfigRepository.getOrCreate()

    expect(config.id).toMatch(/[0-9a-fA-F-]{36}/)
    expect(config.organization_id).toBe('org_default')
    expect(config.site_id).toBe('default_site')
    expect(config.device_id).toBe('default_device')
    expectIsoString(config.created_at)
    expectIsoString(config.updated_at)
  })

  it('returns existing config when one already exists', async () => {
    const firstConfig = await deploymentConfigRepository.getOrCreate()
    const secondConfig = await deploymentConfigRepository.getOrCreate()

    expect(firstConfig.id).toBe(secondConfig.id)
    expect(firstConfig.organization_id).toBe(secondConfig.organization_id)
    expect(firstConfig.site_id).toBe(secondConfig.site_id)
    expect(firstConfig.device_id).toBe(secondConfig.device_id)
  })

  it('updates organization_id only and preserves other fields', async () => {
    const original = await deploymentConfigRepository.getOrCreate()

    await new Promise((r) => setTimeout(r, 5))

    const updated = await deploymentConfigRepository.update({
      organization_id: 'org_test',
    })

    expect(updated.id).not.toBe(original.id)
    expect(updated.organization_id).toBe('org_test')
    expect(updated.site_id).toBe(original.site_id)
    expect(updated.device_id).toBe(original.device_id)
    expect(new Date(updated.created_at).getTime()).toBeGreaterThan(
      new Date(original.created_at).getTime()
    )
  })

  it('updates multiple fields correctly', async () => {
    await deploymentConfigRepository.getOrCreate()

    const updated = await deploymentConfigRepository.update({
      organization_id: 'org_new',
      site_id: 'new_site',
      device_id: 'new_device',
    })

    expect(updated.organization_id).toBe('org_new')
    expect(updated.site_id).toBe('new_site')
    expect(updated.device_id).toBe('new_device')
  })

  it('follows single record paradigm - delete old, create new', async () => {
    const original = await deploymentConfigRepository.getOrCreate()

    await deploymentConfigRepository.update({
      organization_id: 'org_updated',
    })

    const db = getDatabase()
    const allConfigs = await db.select().from(deploymentConfigTable).all()
    expect(allConfigs).toHaveLength(1)
    expect(allConfigs[0].id).not.toBe(original.id)
    expect(allConfigs[0].organization_id).toBe('org_updated')
  })

  it('preserves unchanged fields when updating partial data', async () => {
    const original = await deploymentConfigRepository.getOrCreate()

    const updated = await deploymentConfigRepository.update({
      site_id: 'new_site_only',
    })

    expect(updated.organization_id).toBe(original.organization_id)
    expect(updated.site_id).toBe('new_site_only')
    expect(updated.device_id).toBe(original.device_id)
  })

  it('updates timestamps on each update', async () => {
    const original = await deploymentConfigRepository.getOrCreate()

    await new Promise((r) => setTimeout(r, 10))

    const updated = await deploymentConfigRepository.update({
      organization_id: 'org_time_test',
    })

    expect(new Date(updated.created_at).getTime()).toBeGreaterThan(
      new Date(original.created_at).getTime()
    )
    expect(new Date(updated.updated_at).getTime()).toBeGreaterThan(
      new Date(original.updated_at).getTime()
    )
  })
})
