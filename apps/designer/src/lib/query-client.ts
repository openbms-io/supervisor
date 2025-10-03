import { QueryClient } from '@tanstack/react-query'

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,
        gcTime: 10 * 60 * 1000,
        retry: 3,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        refetchOnWindowFocus: process.env.NODE_ENV === 'production',
        refetchOnMount: false,
      },
      mutations: {
        retry: 2,
        retryDelay: 1000,
      },
    },
  })
}

type QueryParams = Record<string, string | number | boolean | undefined | null>

export const queryKeys = {
  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    list: (params?: QueryParams) =>
      [...queryKeys.projects.lists(), params] as const,
    details: () => [...queryKeys.projects.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
  },
  deploymentConfig: {
    all: ['deploymentConfig'] as const,
    detail: (projectId: string) =>
      [...queryKeys.deploymentConfig.all, 'detail', projectId] as const,
  },
} as const
