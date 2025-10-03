import { renderHook, waitFor } from '@testing-library/react'
import { createTestQueryClient, createHookWrapper } from '@test-utils/render'
import {
  useDeploymentConfig,
  useUpdateDeploymentConfig,
  useOptimisticUpdateDeploymentConfig,
} from './use-deployment-config'
import type { DeploymentConfig } from '@/app/api/projects/[id]/deployment-config/schemas'

describe('useDeploymentConfig hooks', () => {
  const mockFetch = jest.spyOn(global, 'fetch')
  const testProjectId = '550e8400-e29b-41d4-a716-446655440000'

  const mockConfig: DeploymentConfig = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    project_id: testProjectId,
    organization_id: 'org_test',
    site_id: 'test_site',
    iot_device_id: 'test_device',
    created_at: '2025-01-01T00:00:00.000Z',
    updated_at: '2025-01-01T00:00:00.000Z',
  }

  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterAll(() => {
    mockFetch.mockRestore()
  })

  describe('useDeploymentConfig', () => {
    it('should fetch deployment config successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: mockConfig,
        }),
      } as Response)

      const { result } = renderHook(() => useDeploymentConfig(testProjectId), {
        wrapper: createHookWrapper(),
      })

      await waitFor(
        () => {
          expect(result.current.isSuccess).toBe(true)
        },
        { timeout: 3000 }
      )

      expect(result.current.data).toEqual(mockConfig)
      expect(mockFetch).toHaveBeenCalledWith(
        `/api/projects/${testProjectId}/deployment-config`
      )
    })

    it('should handle loading state', () => {
      mockFetch.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      const { result } = renderHook(() => useDeploymentConfig(testProjectId), {
        wrapper: createHookWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
    })

    it('should handle server error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Internal Server Error',
      } as Response)

      const { result } = renderHook(() => useDeploymentConfig(testProjectId), {
        wrapper: createHookWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useDeploymentConfig(testProjectId), {
        wrapper: createHookWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })

    it('should respect custom query options', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: mockConfig,
        }),
      } as Response)

      const { result } = renderHook(
        () => useDeploymentConfig(testProjectId, { enabled: false }),
        {
          wrapper: createHookWrapper(),
        }
      )

      expect(result.current.isFetching).toBe(false)
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('useUpdateDeploymentConfig', () => {
    it('should update deployment config successfully', async () => {
      const updatedConfig = { ...mockConfig, organization_id: 'org_updated' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: updatedConfig,
        }),
      } as Response)

      const { result } = renderHook(
        () => useUpdateDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(),
        }
      )

      const updateData = { organization_id: 'org_updated' }
      result.current.mutate(updateData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(updatedConfig)
      expect(mockFetch).toHaveBeenCalledWith(
        `/api/projects/${testProjectId}/deployment-config`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        }
      )
    })

    it('should handle update error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Validation error',
      } as Response)

      const { result } = renderHook(
        () => useUpdateDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(),
        }
      )

      result.current.mutate({ organization_id: 'invalid' })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })

    it('should call onSuccess callback', async () => {
      const updatedConfig = { ...mockConfig, organization_id: 'org_callback' }
      const onSuccess = jest.fn()

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: updatedConfig,
        }),
      } as Response)

      const { result } = renderHook(
        () => useUpdateDeploymentConfig(testProjectId, { onSuccess }),
        {
          wrapper: createHookWrapper(),
        }
      )

      result.current.mutate({ organization_id: 'org_callback' })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(onSuccess).toHaveBeenCalledWith(
        updatedConfig,
        { organization_id: 'org_callback' },
        undefined
      )
    })
  })

  describe('useOptimisticUpdateDeploymentConfig', () => {
    it('should update UI optimistically', async () => {
      const queryClient = createTestQueryClient()

      // First, populate the cache with initial data
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: mockConfig,
        }),
      } as Response)

      const { result: queryResult } = renderHook(
        () => useDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      // Now test optimistic update
      const updatedConfig = { ...mockConfig, organization_id: 'org_optimistic' }

      // Slow response to test optimistic state
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => ({
                  success: true,
                  config: updatedConfig,
                }),
              } as Response)
            }, 100)
          )
      )

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      // Trigger optimistic update
      mutationResult.current.mutate({ organization_id: 'org_optimistic' })

      // Check optimistic state after a micro task
      await new Promise((resolve) => setTimeout(resolve, 0))

      const optimisticData = queryClient!.getQueryData([
        'deploymentConfig',
        'detail',
        testProjectId,
      ]) as DeploymentConfig

      expect(optimisticData.organization_id).toBe('org_optimistic')

      // Wait for mutation to complete
      await waitFor(() => {
        expect(mutationResult.current.isSuccess).toBe(true)
      })
    })

    it('should rollback on error', async () => {
      const queryClient = createTestQueryClient()

      // First, populate the cache with initial data
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: mockConfig,
        }),
      } as Response)

      const { result: queryResult } = renderHook(
        () => useDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      // Mock error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Validation error',
      } as Response)

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      // Trigger optimistic update that will fail
      mutationResult.current.mutate({ organization_id: 'org_will_fail' })

      // Wait for error
      await waitFor(() => {
        expect(mutationResult.current.isError).toBe(true)
      })

      // Check that data was rolled back to original
      const rolledBackData = queryClient!.getQueryData([
        'deploymentConfig',
        'detail',
        testProjectId,
      ]) as DeploymentConfig

      expect(rolledBackData).toEqual(mockConfig)
    })

    it('should preserve unchanged fields in optimistic update', async () => {
      const queryClient = createTestQueryClient()

      // First, populate the cache with initial data
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: mockConfig,
        }),
      } as Response)

      const { result: queryResult } = renderHook(
        () => useDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      // Mock response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          config: { ...mockConfig, site_id: 'new_site' },
        }),
      } as Response)

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateDeploymentConfig(testProjectId),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      // Update only site_id
      mutationResult.current.mutate({ site_id: 'new_site' })

      // Check optimistic state after a micro task
      await new Promise((resolve) => setTimeout(resolve, 0))

      // Check optimistic state preserves other fields
      const optimisticData = queryClient!.getQueryData([
        'deploymentConfig',
        'detail',
        testProjectId,
      ]) as DeploymentConfig

      expect(optimisticData.site_id).toBe('new_site')
      expect(optimisticData.organization_id).toBe(mockConfig.organization_id)
      expect(optimisticData.iot_device_id).toBe(mockConfig.iot_device_id)
    })
  })
})
