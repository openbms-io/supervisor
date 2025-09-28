import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient } from '@tanstack/react-query'
import { createTestQueryClient, createHookWrapper } from '@test-utils/render'
import {
  useProjects,
  useProject,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  useOptimisticUpdateProject,
  usePrefetchProject,
} from './use-projects'
import type { Project, ProjectListResponse } from '@/app/api/projects/schemas'

describe('useProjects hooks', () => {
  const mockFetch = jest.spyOn(global, 'fetch')

  const mockProject: Project = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Test Project',
    description: 'Test Description',
    workflow_config: '{}',
    created_at: '2025-01-01T00:00:00.000Z',
    updated_at: '2025-01-01T00:00:00.000Z',
  }

  const mockProjectsList: ProjectListResponse = {
    projects: [mockProject],
    total: 1,
    page: 1,
    limit: 20,
    pages: 1,
  }

  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterAll(() => {
    mockFetch.mockRestore()
  })

  describe('useProjects', () => {
    it('should fetch projects list successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockProjectsList,
        }),
      } as Response)

      const { result } = renderHook(() => useProjects(), {
        wrapper: createHookWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockProjectsList)
      expect(mockFetch).toHaveBeenCalledWith('/api/projects')
    })

    it('should handle loading state', () => {
      mockFetch.mockImplementation(() => new Promise(() => {}))

      const { result } = renderHook(() => useProjects(), {
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

      const { result } = renderHook(() => useProjects(), {
        wrapper: createHookWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useProjects(), {
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
          data: mockProjectsList,
        }),
      } as Response)

      const { result } = renderHook(
        () => useProjects(undefined, { enabled: false }),
        {
          wrapper: createHookWrapper(),
        }
      )

      expect(result.current.isFetching).toBe(false)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('should handle query parameters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockProjectsList,
        }),
      } as Response)

      const query = { page: 2, limit: 10, search: 'test' }
      const { result } = renderHook(() => useProjects(query), {
        wrapper: createHookWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/projects?page=2&limit=10&search=test'
      )
    })
  })

  describe('useProject', () => {
    it('should fetch single project successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: mockProject,
        }),
      } as Response)

      const { result } = renderHook(() => useProject(mockProject.id), {
        wrapper: createHookWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockProject)
      expect(mockFetch).toHaveBeenCalledWith(`/api/projects/${mockProject.id}`)
    })

    it('should handle loading state', () => {
      mockFetch.mockImplementation(() => new Promise(() => {}))

      const { result } = renderHook(() => useProject(mockProject.id), {
        wrapper: createHookWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
    })

    it('should not fetch when id is empty', () => {
      const { result } = renderHook(() => useProject(''), {
        wrapper: createHookWrapper(),
      })

      expect(result.current.isFetching).toBe(false)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('should handle server error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => 'Not Found',
      } as Response)

      const { result } = renderHook(() => useProject(mockProject.id), {
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
          project: mockProject,
        }),
      } as Response)

      const { result } = renderHook(
        () => useProject(mockProject.id, { enabled: false }),
        {
          wrapper: createHookWrapper(),
        }
      )

      expect(result.current.isFetching).toBe(false)
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('useCreateProject', () => {
    it('should create project successfully', async () => {
      const newProject = { ...mockProject, name: 'New Project' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: newProject,
        }),
      } as Response)

      const { result } = renderHook(() => useCreateProject(), {
        wrapper: createHookWrapper(),
      })

      const createData = { name: 'New Project', description: 'New Description' }
      result.current.mutate(createData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(newProject)
      expect(mockFetch).toHaveBeenCalledWith('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createData),
      })
    })

    it('should handle creation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Validation error',
      } as Response)

      const { result } = renderHook(() => useCreateProject(), {
        wrapper: createHookWrapper(),
      })

      result.current.mutate({ name: 'Invalid' })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })

    it('should call onSuccess callback', async () => {
      const onSuccess = jest.fn()
      const newProject = { ...mockProject, name: 'Callback Project' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: newProject,
        }),
      } as Response)

      const { result } = renderHook(() => useCreateProject({ onSuccess }), {
        wrapper: createHookWrapper(),
      })

      const createData = { name: 'Callback Project' }
      result.current.mutate(createData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(onSuccess).toHaveBeenCalledWith(newProject, createData, undefined)
    })
  })

  describe('useUpdateProject', () => {
    it('should update project successfully', async () => {
      const updatedProject = { ...mockProject, name: 'Updated Project' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: updatedProject,
        }),
      } as Response)

      const { result } = renderHook(() => useUpdateProject(), {
        wrapper: createHookWrapper(),
      })

      const updateData = {
        params: { id: mockProject.id, data: { name: 'Updated Project' } },
      }
      result.current.mutate(updateData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(updatedProject)
      expect(mockFetch).toHaveBeenCalledWith(
        `/api/projects/${mockProject.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Updated Project' }),
        }
      )
    })

    it('should handle update error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Validation error',
      } as Response)

      const { result } = renderHook(() => useUpdateProject(), {
        wrapper: createHookWrapper(),
      })

      result.current.mutate({
        params: { id: mockProject.id, data: { name: 'Invalid' } },
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })

    it('should call onSuccess callback', async () => {
      const onSuccess = jest.fn()
      const updatedProject = { ...mockProject, name: 'Callback Project' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: updatedProject,
        }),
      } as Response)

      const { result } = renderHook(() => useUpdateProject({ onSuccess }), {
        wrapper: createHookWrapper(),
      })

      const updateData = {
        params: { id: mockProject.id, data: { name: 'Callback Project' } },
      }
      result.current.mutate(updateData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(onSuccess).toHaveBeenCalledWith(
        updatedProject,
        updateData,
        undefined
      )
    })
  })

  describe('useDeleteProject', () => {
    it('should delete project successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
        }),
      } as Response)

      const { result } = renderHook(() => useDeleteProject(), {
        wrapper: createHookWrapper(),
      })

      result.current.mutate(mockProject.id)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        `/api/projects/${mockProject.id}`,
        {
          method: 'DELETE',
        }
      )
    })

    it('should handle deletion error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => 'Not Found',
      } as Response)

      const { result } = renderHook(() => useDeleteProject(), {
        wrapper: createHookWrapper(),
      })

      result.current.mutate(mockProject.id)

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })
  })

  describe('useOptimisticUpdateProject', () => {
    it('should update UI optimistically', async () => {
      const queryClient: QueryClient

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: mockProject,
        }),
      } as Response)

      queryClient = createTestQueryClient()
      const { result: queryResult } = renderHook(
        () => useProject(mockProject.id),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      const updatedProject = { ...mockProject, name: 'Optimistic Project' }

      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => ({
                  success: true,
                  project: updatedProject,
                }),
              } as Response)
            }, 100)
          )
      )

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateProject(),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      mutationResult.current.mutate({
        params: { id: mockProject.id, data: { name: 'Optimistic Project' } },
      })

      await new Promise((resolve) => setTimeout(resolve, 0))

      const optimisticData = queryClient!.getQueryData([
        'projects',
        'detail',
        mockProject.id,
      ]) as Project

      expect(optimisticData.name).toBe('Optimistic Project')

      await waitFor(() => {
        expect(mutationResult.current.isSuccess).toBe(true)
      })
    })

    it('should rollback on error', async () => {
      const queryClient: QueryClient

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: mockProject,
        }),
      } as Response)

      queryClient = createTestQueryClient()
      const { result: queryResult } = renderHook(
        () => useProject(mockProject.id),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Validation error',
      } as Response)

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateProject(),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      mutationResult.current.mutate({
        params: { id: mockProject.id, data: { name: 'Will Fail' } },
      })

      await waitFor(() => {
        expect(mutationResult.current.isError).toBe(true)
      })

      const rolledBackData = queryClient!.getQueryData([
        'projects',
        'detail',
        mockProject.id,
      ]) as Project

      expect(rolledBackData).toEqual(mockProject)
    })

    it('should preserve unchanged fields in optimistic update', async () => {
      const queryClient: QueryClient

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: mockProject,
        }),
      } as Response)

      queryClient = createTestQueryClient()
      const { result: queryResult } = renderHook(
        () => useProject(mockProject.id),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: { ...mockProject, description: 'New Description' },
        }),
      } as Response)

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateProject(),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      mutationResult.current.mutate({
        params: {
          id: mockProject.id,
          data: { description: 'New Description' },
        },
      })

      await new Promise((resolve) => setTimeout(resolve, 0))

      const optimisticData = queryClient!.getQueryData([
        'projects',
        'detail',
        mockProject.id,
      ]) as Project

      expect(optimisticData.description).toBe('New Description')
      expect(optimisticData.name).toBe(mockProject.name)
      expect(optimisticData.workflow_config).toBe(mockProject.workflow_config)
    })

    it('should handle workflow_config serialization', async () => {
      const queryClient: QueryClient

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: mockProject,
        }),
      } as Response)

      queryClient = createTestQueryClient()
      const { result: queryResult } = renderHook(
        () => useProject(mockProject.id),
        {
          wrapper: createHookWrapper(queryClient),
        }
      )

      await waitFor(() => {
        expect(queryResult.current.isSuccess).toBe(true)
      })

      const workflowConfig = { nodes: [], edges: [] }
      const updatedProject = {
        ...mockProject,
        workflow_config: JSON.stringify(workflowConfig),
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: updatedProject,
        }),
      } as Response)

      const { result: mutationResult } = renderHook(
        () => useOptimisticUpdateProject(),
        {
          wrapper: createHookWrapper(queryClient!),
        }
      )

      mutationResult.current.mutate({
        params: {
          id: mockProject.id,
          data: { workflow_config: workflowConfig },
        },
      })

      await new Promise((resolve) => setTimeout(resolve, 0))

      const optimisticData = queryClient!.getQueryData([
        'projects',
        'detail',
        mockProject.id,
      ]) as Project

      expect(optimisticData.workflow_config).toBe(
        JSON.stringify(workflowConfig)
      )
    })
  })

  describe('usePrefetchProject', () => {
    it('should prefetch project data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          project: mockProject,
        }),
      } as Response)

      const queryClient = createTestQueryClient()
      const { result } = renderHook(() => usePrefetchProject(), {
        wrapper: createHookWrapper(queryClient),
      })

      result.current({ id: mockProject.id })

      await waitFor(() => {
        const cachedData = queryClient.getQueryData([
          'projects',
          'detail',
          mockProject.id,
        ])
        expect(cachedData).toEqual(mockProject)
      })

      expect(mockFetch).toHaveBeenCalledWith(`/api/projects/${mockProject.id}`)
    })
  })
})
