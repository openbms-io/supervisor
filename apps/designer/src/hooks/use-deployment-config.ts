import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
} from '@tanstack/react-query'
import {
  DeploymentConfig,
  UpdateDeploymentConfig,
} from '@/app/api/projects/[id]/deployment-config/schemas'

import { deploymentConfigApi } from '../lib/api/deployment-config'
import { queryKeys } from '../lib/query-client'

export function useDeploymentConfig(
  projectId: string,
  options?: Omit<
    UseQueryOptions<DeploymentConfig | null>,
    'queryKey' | 'queryFn'
  >
): ReturnType<typeof useQuery<DeploymentConfig | null>> {
  return useQuery({
    queryKey: queryKeys.deploymentConfig.detail(projectId),
    queryFn: () => deploymentConfigApi.get(projectId),
    enabled: !!projectId,
    ...options,
  })
}

export function useUpdateDeploymentConfig(
  projectId: string,
  options?: UseMutationOptions<DeploymentConfig, Error, UpdateDeploymentConfig>
): ReturnType<
  typeof useMutation<DeploymentConfig, Error, UpdateDeploymentConfig>
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateDeploymentConfig) =>
      deploymentConfigApi.update(projectId, data),
    onSuccess: (updatedConfig) => {
      queryClient.setQueryData(
        queryKeys.deploymentConfig.detail(projectId),
        updatedConfig
      )
    },
    ...options,
  })
}

export function useOptimisticUpdateDeploymentConfig(
  projectId: string,
  options?: Omit<
    UseMutationOptions<
      DeploymentConfig,
      Error,
      UpdateDeploymentConfig,
      { previousConfig: DeploymentConfig | null | undefined }
    >,
    'mutationFn' | 'onMutate' | 'onError' | 'onSettled'
  >
): ReturnType<
  typeof useMutation<
    DeploymentConfig,
    Error,
    UpdateDeploymentConfig,
    { previousConfig: DeploymentConfig | null | undefined }
  >
> {
  const queryClient = useQueryClient()

  return useMutation<
    DeploymentConfig,
    Error,
    UpdateDeploymentConfig,
    { previousConfig: DeploymentConfig | null | undefined }
  >({
    mutationFn: (data: UpdateDeploymentConfig) =>
      deploymentConfigApi.update(projectId, data),
    onMutate: async (updateData: UpdateDeploymentConfig) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.deploymentConfig.detail(projectId),
      })
      const previousConfig = queryClient.getQueryData<DeploymentConfig | null>(
        queryKeys.deploymentConfig.detail(projectId)
      )
      if (previousConfig) {
        const optimisticConfig: DeploymentConfig = {
          ...previousConfig,
          updated_at: new Date().toISOString(),
        }

        if (updateData.organization_id !== undefined) {
          optimisticConfig.organization_id = updateData.organization_id
        }
        if (updateData.site_id !== undefined) {
          optimisticConfig.site_id = updateData.site_id
        }
        if (updateData.iot_device_id !== undefined) {
          optimisticConfig.iot_device_id = updateData.iot_device_id
        }

        queryClient.setQueryData<DeploymentConfig>(
          queryKeys.deploymentConfig.detail(projectId),
          optimisticConfig
        )
      }

      return { previousConfig }
    },
    onError: (err, updateData, context) => {
      if (context?.previousConfig) {
        queryClient.setQueryData(
          queryKeys.deploymentConfig.detail(projectId),
          context.previousConfig
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.deploymentConfig.detail(projectId),
      })
    },
    ...options,
  })
}

export function useDeleteDeploymentConfig(
  projectId: string,
  options?: UseMutationOptions<void, Error, void>
): ReturnType<typeof useMutation<void, Error, void>> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => deploymentConfigApi.delete(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.deploymentConfig.detail(projectId),
      })
    },
    ...options,
  })
}
