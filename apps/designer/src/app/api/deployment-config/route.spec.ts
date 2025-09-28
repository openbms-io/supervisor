/** @jest-environment node */

import { GET, PUT } from './route'
import { NextRequest } from 'next/server'
import { getDatabase, closeDatabase } from '@/lib/db/client'
import { deploymentConfig as deploymentConfigTable } from '@/lib/db/schema'

describe('/api/deployment-config route handlers', () => {
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

  describe('GET /api/deployment-config', () => {
    it('should return default config when none exists', async () => {
      const response = await GET()
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.config).toBeDefined()
      expect(data.config.organization_id).toBe('org_default')
      expect(data.config.site_id).toBe('default_site')
      expect(data.config.device_id).toBe('default_device')
      expect(data.config.id).toMatch(/[0-9a-fA-F-]{36}/)
      expectIsoString(data.config.created_at)
      expectIsoString(data.config.updated_at)
    })

    it('should return existing config when one exists', async () => {
      const firstResponse = await GET()
      const firstData = await firstResponse.json()

      const secondResponse = await GET()
      const secondData = await secondResponse.json()

      expect(secondResponse.status).toBe(200)
      expect(secondData.config.id).toBe(firstData.config.id)
      expect(secondData.config.organization_id).toBe(
        firstData.config.organization_id
      )
      expect(secondData.config.site_id).toBe(firstData.config.site_id)
      expect(secondData.config.device_id).toBe(firstData.config.device_id)
    })
  })

  describe('PUT /api/deployment-config', () => {
    it('should update organization_id successfully', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({ organization_id: 'org_updated' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.config.organization_id).toBe('org_updated')
      expect(data.config.site_id).toBe('default_site')
      expect(data.config.device_id).toBe('default_device')

      const getResponse = await GET()
      const getData = await getResponse.json()
      expect(getData.config.organization_id).toBe('org_updated')
    })

    it('should update site_id successfully', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({ site_id: 'new_site' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.config.site_id).toBe('new_site')
      expect(data.config.organization_id).toBe('org_default')
      expect(data.config.device_id).toBe('default_device')
    })

    it('should update device_id successfully', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({ device_id: 'new_device' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.config.device_id).toBe('new_device')
      expect(data.config.organization_id).toBe('org_default')
      expect(data.config.site_id).toBe('default_site')
    })

    it('should update multiple fields at once', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({
          organization_id: 'org_multi',
          site_id: 'site_multi',
          device_id: 'device_multi',
        }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.config.organization_id).toBe('org_multi')
      expect(data.config.site_id).toBe('site_multi')
      expect(data.config.device_id).toBe('device_multi')
    })

    it('should return 400 for invalid organization_id format', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({ organization_id: 'invalid_no_prefix' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toContain('must start with "org_"')
    })

    it('should return 400 for empty organization_id', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({ organization_id: '' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toContain('Validation error')
    })

    it('should return 400 for empty request body', async () => {
      await GET()

      const mockRequest = {
        json: async () => ({}),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toContain('Validation error')
    })

    it('should preserve unchanged fields during partial update', async () => {
      const initialResponse = await GET()
      const initialData = await initialResponse.json()

      const mockRequest = {
        json: async () => ({ site_id: 'new_site_only' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.config.site_id).toBe('new_site_only')
      expect(data.config.organization_id).toBe(
        initialData.config.organization_id
      )
      expect(data.config.device_id).toBe(initialData.config.device_id)
    })

    it('should follow single record paradigm - new ID on update', async () => {
      const initialResponse = await GET()
      const initialData = await initialResponse.json()
      const initialId = initialData.config.id

      const mockRequest = {
        json: async () => ({ organization_id: 'org_new_id' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.config.id).not.toBe(initialId)
      expect(data.config.organization_id).toBe('org_new_id')

      const db = getDatabase()
      const allConfigs = await db.select().from(deploymentConfigTable).all()
      expect(allConfigs).toHaveLength(1)
      expect(allConfigs[0].id).toBe(data.config.id)
    })

    it('should update timestamps on each update', async () => {
      const initialResponse = await GET()
      const initialData = await initialResponse.json()

      await new Promise((r) => setTimeout(r, 10))

      const mockRequest = {
        json: async () => ({ organization_id: 'org_time_test' }),
      } as NextRequest

      const response = await PUT(mockRequest)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(new Date(data.config.created_at).getTime()).toBeGreaterThan(
        new Date(initialData.config.created_at).getTime()
      )
      expect(new Date(data.config.updated_at).getTime()).toBeGreaterThan(
        new Date(initialData.config.updated_at).getTime()
      )
    })
  })
})
