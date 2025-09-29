/** @jest-environment node */

import { GET, PUT, DELETE } from './route'
import { NextRequest } from 'next/server'
import { getDatabase, closeDatabase } from '@/lib/db/client'
import {
  deploymentConfig as deploymentConfigTable,
  projects as projectsTable,
} from '@/lib/db/schema'

describe('/api/projects/[id]/deployment-config route handlers', () => {
  const testProjectId = '550e8400-e29b-41d4-a716-446655440000'

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

  describe('GET /api/projects/[id]/deployment-config', () => {
    it('should return null config when none exists', async () => {
      const request = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`
      )
      const params = Promise.resolve({ id: testProjectId })
      const response = await GET(request, { params })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.config).toBeNull()
    })

    it('should return existing config when one exists', async () => {
      // Create config first
      const updateRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          body: JSON.stringify({
            organization_id: 'org_test',
            site_id: 'test_site',
            iot_device_id: 'test_device',
          }),
        }
      )
      const params = Promise.resolve({ id: testProjectId })
      await PUT(updateRequest, { params })

      // Now get it
      const getRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`
      )
      const response = await GET(getRequest, { params })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.config).toBeDefined()
      expect(data.config.project_id).toBe(testProjectId)
      expect(data.config.organization_id).toBe('org_test')
      expect(data.config.site_id).toBe('test_site')
      expect(data.config.iot_device_id).toBe('test_device')
      expect(data.config.id).toMatch(/[0-9a-fA-F-]{36}/)
      expectIsoString(data.config.created_at)
      expectIsoString(data.config.updated_at)
    })
  })

  describe('PUT /api/projects/[id]/deployment-config', () => {
    it('should create new config when none exists', async () => {
      const request = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          body: JSON.stringify({
            organization_id: 'org_new',
            site_id: 'new_site',
            iot_device_id: 'new_device',
          }),
        }
      )
      const params = Promise.resolve({ id: testProjectId })
      const response = await PUT(request, { params })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.config.project_id).toBe(testProjectId)
      expect(data.config.organization_id).toBe('org_new')
      expect(data.config.site_id).toBe('new_site')
      expect(data.config.iot_device_id).toBe('new_device')
      expectIsoString(data.config.created_at)
      expectIsoString(data.config.updated_at)
    })

    it('should update existing config', async () => {
      // Create initial config
      const createRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          body: JSON.stringify({
            organization_id: 'org_initial',
            site_id: 'initial_site',
            iot_device_id: 'initial_device',
          }),
        }
      )
      const params = Promise.resolve({ id: testProjectId })
      const createResponse = await PUT(createRequest, { params })
      const initialData = await createResponse.json()

      await new Promise((r) => setTimeout(r, 5))

      // Update config
      const updateRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          body: JSON.stringify({
            organization_id: 'org_updated',
            site_id: 'updated_site',
            iot_device_id: 'updated_device',
          }),
        }
      )
      const updateResponse = await PUT(updateRequest, { params })
      const data = await updateResponse.json()

      expect(updateResponse.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.config.id).toBe(initialData.config.id) // Same record
      expect(data.config.organization_id).toBe('org_updated')
      expect(data.config.site_id).toBe('updated_site')
      expect(data.config.iot_device_id).toBe('updated_device')
      expect(new Date(data.config.updated_at).getTime()).toBeGreaterThan(
        new Date(initialData.config.updated_at).getTime()
      )
    })

    it('should validate required fields', async () => {
      const request = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          body: JSON.stringify({
            organization_id: '', // Invalid empty string
            site_id: 'test_site',
            iot_device_id: 'test_device',
          }),
        }
      )
      const params = Promise.resolve({ id: testProjectId })
      const response = await PUT(request, { params })
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toContain('Validation error')
    })
  })

  describe('DELETE /api/projects/[id]/deployment-config', () => {
    it('should delete existing config', async () => {
      // Create config first
      const createRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          body: JSON.stringify({
            organization_id: 'org_test',
            site_id: 'test_site',
            iot_device_id: 'test_device',
          }),
        }
      )
      const params = Promise.resolve({ id: testProjectId })
      await PUT(createRequest, { params })

      // Delete it
      const deleteRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'DELETE',
        }
      )
      const response = await DELETE(deleteRequest, { params })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)

      // Verify it's gone
      const getRequest = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`
      )
      const getResponse = await GET(getRequest, { params })
      const getData = await getResponse.json()
      expect(getData.config).toBeNull()
    })

    it('should succeed even if no config exists', async () => {
      const request = new NextRequest(
        `http://localhost:3000/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'DELETE',
        }
      )
      const params = Promise.resolve({ id: testProjectId })
      const response = await DELETE(request, { params })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
    })
  })
})
