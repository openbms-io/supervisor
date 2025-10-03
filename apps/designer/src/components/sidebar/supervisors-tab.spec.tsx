import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SupervisorsTab } from './supervisors-tab'
import {
  useDeploymentConfig,
  useUpdateDeploymentConfig,
} from '@/hooks/use-deployment-config'
import { useFlowStore } from '@/store/use-flow-store'

jest.mock('@/hooks/use-deployment-config')
jest.mock('@/store/use-flow-store')

const mockUseDeploymentConfig = useDeploymentConfig as jest.MockedFunction<
  typeof useDeploymentConfig
>
const mockUseUpdateDeploymentConfig =
  useUpdateDeploymentConfig as jest.MockedFunction<
    typeof useUpdateDeploymentConfig
  >
const mockUseFlowStore = useFlowStore as unknown as jest.Mock

describe('SupervisorsTab', () => {
  const defaultProps = {
    projectId: 'project-123',
  }

  const mockDeploymentConfig = {
    id: 'config-1',
    project_id: 'project-123',
    organization_id: 'org_test',
    site_id: 'site-123',
    iot_device_id: 'device-456',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    mockUseFlowStore.mockImplementation((selector) => {
      const state = {
        connectionStatus: 'disconnected' as const,
        brokerHealth: {
          status: 'unknown' as const,
          lastHeartbeat: null,
          lastHeartbeatTimestamp: null,
        },
        lastError: undefined,
      }
      return selector(state)
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering States', () => {
    it('should show loading state while fetching config', () => {
      mockUseDeploymentConfig.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('should show "No Supervisor Configured" when no config', () => {
      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('No Supervisor Configured')).toBeInTheDocument()
      expect(
        screen.getByText(/Configure deployment settings/i)
      ).toBeInTheDocument()
    })

    it('should show "Configure Supervisor" button when no config', () => {
      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      ).toBeInTheDocument()
    })

    it('should show deployment config when configured', () => {
      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('Supervisor Configured')).toBeInTheDocument()
      expect(screen.getByText('org_test')).toBeInTheDocument()
      expect(screen.getByText('site-123')).toBeInTheDocument()
      expect(screen.getByText('device-456')).toBeInTheDocument()
    })

    it('should show edit button when config exists', () => {
      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      const editButton = screen.getByRole('button', { name: '' })
      expect(editButton).toBeInTheDocument()
    })
  })

  describe('Configuration Form', () => {
    it('should show form when "Configure Supervisor" is clicked', async () => {
      const user = userEvent.setup()

      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      await user.click(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      )

      expect(screen.getByPlaceholderText('org_example')).toBeInTheDocument()
      expect(screen.getAllByPlaceholderText('uuid')).toHaveLength(2)
    })

    it('should disable save button when fields are empty', async () => {
      const user = userEvent.setup()

      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      await user.click(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      )

      const saveButton = screen.getByRole('button', { name: /Save/i })
      expect(saveButton).toBeDisabled()
    })

    it('should disable save button when organization_id does not start with "org_"', async () => {
      const user = userEvent.setup()

      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      await user.click(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      )

      const orgInput = screen.getByPlaceholderText('org_example')
      const [siteInput, deviceInput] = screen.getAllByPlaceholderText('uuid')

      await user.type(orgInput, 'invalid_org')
      await user.type(siteInput, 'site-123')
      await user.type(deviceInput, 'device-456')

      const saveButton = screen.getByRole('button', { name: /Save/i })
      expect(saveButton).toBeDisabled()
    })

    it('should enable save button when all fields are valid', async () => {
      const user = userEvent.setup()

      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      await user.click(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      )

      const orgInput = screen.getByPlaceholderText('org_example')
      const [siteInput, deviceInput] = screen.getAllByPlaceholderText('uuid')

      await user.type(orgInput, 'org_test')
      await user.type(siteInput, 'site-123')
      await user.type(deviceInput, 'device-456')

      const saveButton = screen.getByRole('button', { name: /Save/i })
      expect(saveButton).not.toBeDisabled()
    })

    it('should call update mutation on save', async () => {
      const user = userEvent.setup()
      const mockMutateAsync = jest.fn().mockResolvedValue(mockDeploymentConfig)

      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      await user.click(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      )

      const orgInput = screen.getByPlaceholderText('org_example')
      const [siteInput, deviceInput] = screen.getAllByPlaceholderText('uuid')

      await user.type(orgInput, 'org_test')
      await user.type(siteInput, 'site-123')
      await user.type(deviceInput, 'device-456')

      await user.click(screen.getByRole('button', { name: /Save/i }))

      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org_test',
        site_id: 'site-123',
        iot_device_id: 'device-456',
      })
    })

    it('should reset form on cancel', async () => {
      const user = userEvent.setup()

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      // Click edit button
      const editButtons = screen.getAllByRole('button')
      await user.click(editButtons[editButtons.length - 1])

      // Wait for form to appear and change a field
      await waitFor(() => {
        expect(screen.getByPlaceholderText('org_example')).toBeInTheDocument()
      })

      const orgInput = screen.getByPlaceholderText('org_example')
      await user.clear(orgInput)
      await user.type(orgInput, 'org_changed')

      // Click cancel
      await user.click(screen.getByRole('button', { name: /Cancel/i }))

      // Should show original config again
      await waitFor(() => {
        expect(screen.getByText('org_test')).toBeInTheDocument()
      })
    })

    it('should show "Saving..." during submission', async () => {
      const user = userEvent.setup()
      const mockMutateAsync = jest.fn(() => new Promise(() => {})) // Never resolves

      mockUseDeploymentConfig.mockReturnValue({
        data: null,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      await user.click(
        screen.getByRole('button', { name: /Configure Supervisor/i })
      )

      const orgInput = screen.getByPlaceholderText('org_example')
      const [siteInput, deviceInput] = screen.getAllByPlaceholderText('uuid')

      await user.type(orgInput, 'org_test')
      await user.type(siteInput, 'site-123')
      await user.type(deviceInput, 'device-456')

      // The "Saving..." text is shown when isPending is true
      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })
  })

  describe('MQTT Status Display', () => {
    it('should show connection status badge for connected', () => {
      mockUseFlowStore.mockImplementation((selector) => {
        const state = {
          connectionStatus: 'connected' as const,
          brokerHealth: {
            status: 'unknown' as const,
            lastHeartbeat: null,
            lastHeartbeatTimestamp: null,
          },
          lastError: undefined,
        }
        return selector(state)
      })

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('connected')).toBeInTheDocument()
    })

    it('should show broker health badge as healthy', () => {
      mockUseFlowStore.mockImplementation((selector) => {
        const state = {
          connectionStatus: 'connected' as const,
          brokerHealth: {
            status: 'healthy' as const,
            lastHeartbeat: {
              cpu_usage_percent: 10.5,
              memory_usage_percent: 75.2,
              disk_usage_percent: 45.3,
              temperature_celsius: null,
              uptime_seconds: 666,
              load_average: 1.5,
              monitoring_status: 'active',
              mqtt_connection_status: 'connected',
              bacnet_connection_status: null,
              bacnet_devices_connected: null,
              bacnet_points_monitored: null,
              timestamp: Date.now() / 1000,
              organization_id: 'org_test',
              site_id: 'site-123',
              iot_device_id: 'device-456',
            },
            lastHeartbeatTimestamp: Date.now(),
          },
          lastError: undefined,
        }
        return selector(state)
      })

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('healthy')).toBeInTheDocument()
    })

    it('should display uptime in human-readable format', () => {
      mockUseFlowStore.mockImplementation((selector) => {
        const state = {
          connectionStatus: 'connected' as const,
          brokerHealth: {
            status: 'healthy' as const,
            lastHeartbeat: {
              cpu_usage_percent: 10.5,
              memory_usage_percent: 75.2,
              disk_usage_percent: 45.3,
              temperature_celsius: null,
              uptime_seconds: 666, // Should display as "11m 6s"
              load_average: 1.5,
              monitoring_status: 'active',
              mqtt_connection_status: 'connected',
              bacnet_connection_status: null,
              bacnet_devices_connected: null,
              bacnet_points_monitored: null,
              timestamp: Date.now() / 1000,
              organization_id: 'org_test',
              site_id: 'site-123',
              iot_device_id: 'device-456',
            },
            lastHeartbeatTimestamp: Date.now(),
          },
          lastError: undefined,
        }
        return selector(state)
      })

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('11m 6s')).toBeInTheDocument()
    })

    it('should display monitoring status badge', () => {
      mockUseFlowStore.mockImplementation((selector) => {
        const state = {
          connectionStatus: 'connected' as const,
          brokerHealth: {
            status: 'healthy' as const,
            lastHeartbeat: {
              cpu_usage_percent: 10.5,
              memory_usage_percent: 75.2,
              disk_usage_percent: 45.3,
              temperature_celsius: null,
              uptime_seconds: 666,
              load_average: 1.5,
              monitoring_status: 'active',
              mqtt_connection_status: 'connected',
              bacnet_connection_status: null,
              bacnet_devices_connected: null,
              bacnet_points_monitored: null,
              timestamp: Date.now() / 1000,
              organization_id: 'org_test',
              site_id: 'site-123',
              iot_device_id: 'device-456',
            },
            lastHeartbeatTimestamp: Date.now(),
          },
          lastError: undefined,
        }
        return selector(state)
      })

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('active')).toBeInTheDocument()
    })

    it('should show "Waiting for heartbeat..." when connected but no data', () => {
      mockUseFlowStore.mockImplementation((selector) => {
        const state = {
          connectionStatus: 'connected' as const,
          brokerHealth: {
            status: 'unknown' as const,
            lastHeartbeat: null,
            lastHeartbeatTimestamp: null,
          },
          lastError: undefined,
        }
        return selector(state)
      })

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(
        screen.getByText(/Waiting for heartbeat from supervisor/i)
      ).toBeInTheDocument()
    })

    it('should show error message when lastError exists', () => {
      mockUseFlowStore.mockImplementation((selector) => {
        const state = {
          connectionStatus: 'error' as const,
          brokerHealth: {
            status: 'unhealthy' as const,
            lastHeartbeat: null,
            lastHeartbeatTimestamp: null,
          },
          lastError: 'Connection failed: timeout',
        }
        return selector(state)
      })

      mockUseDeploymentConfig.mockReturnValue({
        data: mockDeploymentConfig,
        isLoading: false,
      } as any)

      mockUseUpdateDeploymentConfig.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
      } as any)

      render(<SupervisorsTab {...defaultProps} />)

      expect(screen.getByText('Connection failed: timeout')).toBeInTheDocument()
    })
  })
})
