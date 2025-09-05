import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
} from '@tanstack/react-query'
import {
  Project,
  CreateProject,
  UpdateProject,
  ProjectQuery,
  ProjectListResponse,
} from '@/app/api/projects/schemas'

import { projectsApi } from '../lib/api/projects'
import { queryKeys } from '../lib/query-client'

export function useProjects(
  query?: ProjectQuery,
  options?: Omit<UseQueryOptions<ProjectListResponse>, 'queryKey' | 'queryFn'>
): ReturnType<typeof useQuery<ProjectListResponse>> {
  return useQuery({
    queryKey: queryKeys.projects.list(query),
    queryFn: () => projectsApi.list(query),
    ...options,
  })
}

export function useProject(
  id: string,
  options?: Omit<UseQueryOptions<Project>, 'queryKey' | 'queryFn'>
): ReturnType<typeof useQuery<Project>> {
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
    ...options,
  })
}

export function useCreateProject(
  options?: UseMutationOptions<Project, Error, CreateProject>
): ReturnType<typeof useMutation<Project, Error, CreateProject>> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProject) => projectsApi.create(data),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists(),
      })
      queryClient.setQueryData(
        queryKeys.projects.detail(newProject.id),
        newProject
      )
    },
    ...options,
  })
}

export function useUpdateProject(
  options?: UseMutationOptions<
    Project,
    Error,
    { params: { id: string; data: UpdateProject } }
  >
): ReturnType<
  typeof useMutation<
    Project,
    Error,
    { params: { id: string; data: UpdateProject } }
  >
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ params }: { params: { id: string; data: UpdateProject } }) =>
      projectsApi.update(params.id, params.data),
    onSuccess: (updatedProject, { params }) => {
      queryClient.setQueryData(
        queryKeys.projects.detail(params.id),
        updatedProject
      )
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists(),
      })
    },
    ...options,
  })
}

export function useDeleteProject(
  options?: UseMutationOptions<void, Error, string>
): ReturnType<typeof useMutation<void, Error, string>> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.removeQueries({
        queryKey: queryKeys.projects.detail(deletedId),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists(),
      })
    },
    ...options,
  })
}

export function useOptimisticUpdateProject(
  options?: Omit<
    UseMutationOptions<
      Project,
      Error,
      { params: { id: string; data: UpdateProject } },
      { previousProject: Project | undefined }
    >,
    'mutationFn' | 'onMutate' | 'onError' | 'onSettled'
  >
): ReturnType<
  typeof useMutation<
    Project,
    Error,
    { params: { id: string; data: UpdateProject } },
    { previousProject: Project | undefined }
  >
> {
  const queryClient = useQueryClient()

  return useMutation<
    Project,
    Error,
    { params: { id: string; data: UpdateProject } },
    { previousProject: Project | undefined }
  >({
    mutationFn: ({ params }: { params: { id: string; data: UpdateProject } }) =>
      projectsApi.update(params.id, params.data),
    onMutate: async ({
      params,
    }: {
      params: { id: string; data: UpdateProject }
    }) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.projects.detail(params.id),
      })
      const previousProject = queryClient.getQueryData<Project>(
        queryKeys.projects.detail(params.id)
      )
      if (previousProject) {
        const updatedProject: Project = {
          ...previousProject,
          updated_at: new Date().toISOString(),
        }

        if (params.data.name !== undefined) {
          updatedProject.name = params.data.name
        }
        if (params.data.description !== undefined) {
          updatedProject.description = params.data.description
        }
        if (params.data.flow_config !== undefined) {
          updatedProject.flow_config = JSON.stringify(params.data.flow_config)
        }

        queryClient.setQueryData<Project>(
          queryKeys.projects.detail(params.id),
          updatedProject
        )
      }

      return { previousProject }
    },
    onError: (err, { params }, context) => {
      if (context?.previousProject) {
        queryClient.setQueryData(
          queryKeys.projects.detail(params.id),
          context.previousProject
        )
      }
    },
    onSettled: (_, __, { params }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(params.id),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists(),
      })
    },
    ...options,
  })
}

export function usePrefetchProject(): ({ id }: { id: string }) => void {
  const queryClient = useQueryClient()

  return ({ id }: { id: string }): void => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.projects.detail(id),
      queryFn: () => projectsApi.get(id),
      staleTime: 5 * 60 * 1000,
    })
  }
}
