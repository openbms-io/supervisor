/** @jest-environment node */

import { deploymentConfigRepository } from './deployment-config'
import { closeDatabase, getDatabase } from './client'
import {
  deploymentConfig as deploymentConfigTable,
  projects as projectsTable,
} from './schema'
import { eq } from 'drizzle-orm'

describe('DeploymentConfigRepository (SQLite + Drizzle)', () => {
  const testProjectId = 'test-project-123'

  beforeEach(async () => {
    const db = getDatabase()
    await db.delete(deploymentConfigTable).run()
    await db.delete(projectsTable).run()

    // Create a test project
    await db
      .insert(projectsTable)
      .values({
        id: testProjectId,
        name: 'Test Project',
        description: null,
        workflow_config: '{}',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .run()
  })

  afterAll(() => {
    closeDatabase()
  })

  function expectIsoString(value: unknown): asserts value is string {
    expect(typeof value).toBe('string')
    expect(() => new Date(value as string)).not.toThrow()
  }

  it('returns null when no config exists for project', async () => {
    const config =
      await deploymentConfigRepository.getByProjectId(testProjectId)
    expect(config).toBeNull()
  })

  it('creates new config for project', async () => {
    const configData = {
      organization_id: 'org_test',
      site_id: 'test_site',
      iot_device_id: 'test_device',
    }

    const config = await deploymentConfigRepository.createOrUpdate(
      testProjectId,
      configData
    )

    expect(config.id).toMatch(/[0-9a-fA-F-]{36}/)
    expect(config.project_id).toBe(testProjectId)
    expect(config.organization_id).toBe('org_test')
    expect(config.site_id).toBe('test_site')
    expect(config.iot_device_id).toBe('test_device')
    expectIsoString(config.created_at)
    expectIsoString(config.updated_at)
  })

  it('updates existing config for project', async () => {
    const initialData = {
      organization_id: 'org_initial',
      site_id: 'initial_site',
      iot_device_id: 'initial_device',
    }

    const original = await deploymentConfigRepository.createOrUpdate(
      testProjectId,
      initialData
    )

    await new Promise((r) => setTimeout(r, 5))

    const updateData = {
      organization_id: 'org_updated',
      site_id: 'updated_site',
      iot_device_id: 'updated_device',
    }

    const updated = await deploymentConfigRepository.createOrUpdate(
      testProjectId,
      updateData
    )

    expect(updated.id).toBe(original.id) // Same record, updated
    expect(updated.project_id).toBe(testProjectId)
    expect(updated.organization_id).toBe('org_updated')
    expect(updated.site_id).toBe('updated_site')
    expect(updated.iot_device_id).toBe('updated_device')
    expect(new Date(updated.updated_at).getTime()).toBeGreaterThan(
      new Date(original.updated_at).getTime()
    )
  })

  it('updates only specified fields and preserves others', async () => {
    const initialData = {
      organization_id: 'org_initial',
      site_id: 'initial_site',
      iot_device_id: 'initial_device',
    }

    const original = await deploymentConfigRepository.createOrUpdate(
      testProjectId,
      initialData
    )

    const partialUpdate = {
      organization_id: 'org_partial',
    }

    const updated = await deploymentConfigRepository.createOrUpdate(
      testProjectId,
      partialUpdate
    )

    expect(updated.id).toBe(original.id)
    expect(updated.organization_id).toBe('org_partial')
    expect(updated.site_id).toBe('initial_site') // Preserved
    expect(updated.iot_device_id).toBe('initial_device') // Preserved
  })

  it('deletes config for project', async () => {
    const configData = {
      organization_id: 'org_test',
      site_id: 'test_site',
      iot_device_id: 'test_device',
    }

    await deploymentConfigRepository.createOrUpdate(testProjectId, configData)

    let config = await deploymentConfigRepository.getByProjectId(testProjectId)
    expect(config).not.toBeNull()

    await deploymentConfigRepository.delete(testProjectId)

    config = await deploymentConfigRepository.getByProjectId(testProjectId)
    expect(config).toBeNull()
  })

  it('enforces unique constraint per project', async () => {
    const db = getDatabase()

    const configData = {
      organization_id: 'org_test',
      site_id: 'test_site',
      iot_device_id: 'test_device',
    }

    await deploymentConfigRepository.createOrUpdate(testProjectId, configData)

    // Verify only one config exists for the project
    const allConfigs = await db
      .select()
      .from(deploymentConfigTable)
      .where(eq(deploymentConfigTable.project_id, testProjectId))
      .all()
    expect(allConfigs).toHaveLength(1)
  })
})
