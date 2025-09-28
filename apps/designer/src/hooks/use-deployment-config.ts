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
} from '@/app/api/deployment-config/schemas'

import { deploymentConfigApi } from '../lib/api/deployment-config'
import { queryKeys } from '../lib/query-client'

export function useDeploymentConfig(
  options?: Omit<UseQueryOptions<DeploymentConfig>, 'queryKey' | 'queryFn'>
): ReturnType<typeof useQuery<DeploymentConfig>> {
  return useQuery({
    queryKey: queryKeys.deploymentConfig.detail(),
    queryFn: () => deploymentConfigApi.get(),
    ...options,
  })
}

export function useUpdateDeploymentConfig(
  options?: UseMutationOptions<DeploymentConfig, Error, UpdateDeploymentConfig>
): ReturnType<
  typeof useMutation<DeploymentConfig, Error, UpdateDeploymentConfig>
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateDeploymentConfig) =>
      deploymentConfigApi.update(data),
    onSuccess: (updatedConfig) => {
      queryClient.setQueryData(
        queryKeys.deploymentConfig.detail(),
        updatedConfig
      )
    },
    ...options,
  })
}

export function useOptimisticUpdateDeploymentConfig(
  options?: Omit<
    UseMutationOptions<
      DeploymentConfig,
      Error,
      UpdateDeploymentConfig,
      { previousConfig: DeploymentConfig | undefined }
    >,
    'mutationFn' | 'onMutate' | 'onError' | 'onSettled'
  >
): ReturnType<
  typeof useMutation<
    DeploymentConfig,
    Error,
    UpdateDeploymentConfig,
    { previousConfig: DeploymentConfig | undefined }
  >
> {
  const queryClient = useQueryClient()

  return useMutation<
    DeploymentConfig,
    Error,
    UpdateDeploymentConfig,
    { previousConfig: DeploymentConfig | undefined }
  >({
    mutationFn: (data: UpdateDeploymentConfig) =>
      deploymentConfigApi.update(data),
    onMutate: async (updateData: UpdateDeploymentConfig) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.deploymentConfig.detail(),
      })
      const previousConfig = queryClient.getQueryData<DeploymentConfig>(
        queryKeys.deploymentConfig.detail()
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
        if (updateData.device_id !== undefined) {
          optimisticConfig.device_id = updateData.device_id
        }

        queryClient.setQueryData<DeploymentConfig>(
          queryKeys.deploymentConfig.detail(),
          optimisticConfig
        )
      }

      return { previousConfig }
    },
    onError: (err, updateData, context) => {
      if (context?.previousConfig) {
        queryClient.setQueryData(
          queryKeys.deploymentConfig.detail(),
          context.previousConfig
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.deploymentConfig.detail(),
      })
    },
    ...options,
  })
}
