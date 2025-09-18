import React from 'react'
import { render as rtlRender } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { RenderOptions } from '@testing-library/react'

// Create a test query client with defaults suitable for testing
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Turn off retries to make tests faster and more predictable
        retry: false,
        // Don't refetch on window focus during tests
        refetchOnWindowFocus: false,
        // Set stale time to 0 to always refetch when needed
        staleTime: 0,
      },
      mutations: {
        // Turn off retries for mutations too
        retry: false,
      },
    },
  })
}

interface ExtendedRenderOptions extends RenderOptions {
  queryClient?: QueryClient
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    queryClient = createTestQueryClient(),
    ...options
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }

  return {
    ...rtlRender(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  }
}

// Export the test query client creator for direct use in tests
export { createTestQueryClient }

export * from '@testing-library/react'
export { renderWithProviders as render }
