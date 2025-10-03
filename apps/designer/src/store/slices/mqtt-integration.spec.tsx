import { render, screen, waitFor } from '@testing-library/react'
import mqtt from 'mqtt'
import { SupervisorsTab } from '@/components/sidebar/supervisors-tab'
import {
  useDeploymentConfig,
  useUpdateDeploymentConfig,
} from '@/hooks/use-deployment-config'
import { useFlowStore } from '@/store/use-flow-store'
import { getMqttBus } from '@/lib/mqtt/mqtt-bus'

jest.mock('mqtt', () => ({
  __esModule: true,
  default: {
    connect: jest.fn(),
  },
}))

jest.mock('uuid', () => ({
  v4: jest.fn(() => 'test-correlation-id'),
}))

jest.mock('@/hooks/use-deployment-config')

const mockUseDeploymentConfig = useDeploymentConfig as jest.MockedFunction<
  typeof useDeploymentConfig
>
const mockUseUpdateDeploymentConfig =
  useUpdateDeploymentConfig as jest.MockedFunction<
    typeof useUpdateDeploymentConfig
  >

describe('MQTT Integration - Full Lifecycle', () => {
  let mockClient: any

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
    jest.useFakeTimers()

    mockClient = {
      on: jest.fn(),
      subscribe: jest.fn(),
      publish: jest.fn(),
      end: jest.fn(),
      connected: false,
    }
    ;(mqtt.connect as jest.Mock).mockReturnValue(mockClient)

    mockUseDeploymentConfig.mockReturnValue({
      data: mockDeploymentConfig,
      isLoading: false,
    } as any)

    mockUseUpdateDeploymentConfig.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
    } as any)
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
    jest.clearAllMocks()
  })

  describe('Full Connection Lifecycle', () => {
    it('should complete full MQTT lifecycle with heartbeat', async () => {
      // Render component
      render(<SupervisorsTab projectId="project-123" />)

      // Step 1: Verify initial state
      expect(screen.getByText('Supervisor Configured')).toBeInTheDocument()
      expect(screen.getByText('org_test')).toBeInTheDocument()

      // Step 2: Start MQTT connection using the actual store
      useFlowStore.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      // Step 3: Simulate MQTT client connection
      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]

      mockClient.connected = true
      connectHandler()

      // Step 4: Verify connection status changes to 'connected'
      await waitFor(() => {
        expect(useFlowStore.getState().connectionStatus).toBe('connected')
      })

      await waitFor(() => {
        expect(screen.getByText('connected')).toBeInTheDocument()
      })

      // Step 5: Simulate BMS heartbeat message on correct topic
      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]

      const heartbeatPayload = {
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
      }

      messageHandler(
        'iot/global/org_test/site-123/device-456/status/heartbeat',
        Buffer.from(JSON.stringify(heartbeatPayload)),
        { properties: {} }
      )

      // Step 6: Verify UI shows heartbeat data
      await waitFor(() => {
        expect(screen.getByText('healthy')).toBeInTheDocument()
      })

      // Step 7: Verify broker health shows 'healthy'
      expect(useFlowStore.getState().brokerHealth.status).toBe('healthy')

      // Step 8: Verify uptime displays correctly (666s = "11m 6s")
      await waitFor(() => {
        expect(screen.getByText('11m 6s')).toBeInTheDocument()
      })

      // Step 9: Verify monitoring status
      await waitFor(() => {
        expect(screen.getByText('active')).toBeInTheDocument()
      })

      // Step 10: Stop MQTT connection
      useFlowStore.getState().stopMqtt()

      // Step 11: Verify cleanup and status reset to 'disconnected'
      expect(mockClient.end).toHaveBeenCalledWith(true)
      expect(useFlowStore.getState().connectionStatus).toBe('disconnected')

      // Step 12: Verify broker health resets to 'unknown'
      expect(useFlowStore.getState().brokerHealth.status).toBe('unknown')
    })
  })

  describe('Heartbeat Timeout', () => {
    it('should mark broker unhealthy after 60s silence', async () => {
      // Start MQTT connection
      useFlowStore.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      // Simulate connection
      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]

      mockClient.connected = true
      connectHandler()

      // Send initial heartbeat
      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]

      const heartbeat = {
        cpu_usage_percent: 10.5,
        memory_usage_percent: 75.2,
        disk_usage_percent: 45.3,
        temperature_celsius: null,
        uptime_seconds: 100,
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
      }

      messageHandler(
        'iot/global/org_test/site-123/device-456/status/heartbeat',
        Buffer.from(JSON.stringify(heartbeat)),
        { properties: {} }
      )

      // Verify broker health is 'healthy'
      expect(useFlowStore.getState().brokerHealth.status).toBe('healthy')

      // Advance time by 65 seconds (past 60s threshold)
      jest.advanceTimersByTime(65_000)

      // Verify broker health changes to 'unhealthy'
      expect(useFlowStore.getState().brokerHealth.status).toBe('unhealthy')

      // Send new heartbeat
      const newHeartbeat = {
        ...heartbeat,
        uptime_seconds: 165,
        timestamp: Date.now() / 1000,
      }

      messageHandler(
        'iot/global/org_test/site-123/device-456/status/heartbeat',
        Buffer.from(JSON.stringify(newHeartbeat)),
        { properties: {} }
      )

      // Verify broker health returns to 'healthy'
      expect(useFlowStore.getState().brokerHealth.status).toBe('healthy')
    })

    it('should remain healthy when heartbeats continue within 60s', async () => {
      // Start MQTT connection
      useFlowStore.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      // Simulate connection
      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]

      mockClient.connected = true
      connectHandler()

      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]

      // Send heartbeats every 30 seconds for 5 iterations
      for (let i = 0; i < 5; i++) {
        const heartbeat = {
          cpu_usage_percent: 10.5,
          memory_usage_percent: 75.2,
          disk_usage_percent: 45.3,
          temperature_celsius: null,
          uptime_seconds: 100 + i * 30,
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
        }

        messageHandler(
          'iot/global/org_test/site-123/device-456/status/heartbeat',
          Buffer.from(JSON.stringify(heartbeat)),
          { properties: {} }
        )

        jest.advanceTimersByTime(30_000)
      }

      // Verify broker health remains 'healthy'
      expect(useFlowStore.getState().brokerHealth.status).toBe('healthy')
    })
  })

  describe('Connection Status Updates', () => {
    it('should update UI when connection status changes', async () => {
      render(<SupervisorsTab projectId="project-123" />)

      // Start connection
      useFlowStore.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      // Should show connecting
      await waitFor(() => {
        expect(useFlowStore.getState().connectionStatus).toBe('connecting')
      })

      // Simulate successful connection
      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]

      mockClient.connected = true
      connectHandler()

      // Should show connected
      await waitFor(() => {
        expect(useFlowStore.getState().connectionStatus).toBe('connected')
      })

      await waitFor(() => {
        expect(screen.getByText('connected')).toBeInTheDocument()
      })
    })

    it('should show error state on connection error', async () => {
      render(<SupervisorsTab projectId="project-123" />)

      // Start connection
      useFlowStore.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      // Simulate connection error
      const errorHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'error'
      )?.[1]

      errorHandler(new Error('Connection failed'))

      // Should show error status
      await waitFor(() => {
        expect(useFlowStore.getState().connectionStatus).toBe('error')
      })

      await waitFor(() => {
        expect(screen.getByText('error')).toBeInTheDocument()
      })
    })
  })

  describe('Point Bulk Stream', () => {
    it('should receive and process point_bulk messages', async () => {
      // Start MQTT connection
      useFlowStore.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      // Simulate connection
      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]

      mockClient.connected = true
      connectHandler()

      // Create observable for point bulk stream
      const pointBulkMessages: any[] = []
      const subscription = getMqttBus().pointBulkStream$.subscribe((msg) =>
        pointBulkMessages.push(msg)
      )

      // Send point_bulk message
      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]

      const pointBulkPayload = {
        controller_id: 'ctrl-1',
        points: [
          { iot_device_point_id: 'point-1', present_value: 23.5 },
          { iot_device_point_id: 'point-2', present_value: 18.2 },
        ],
      }

      messageHandler(
        'iot/global/org_test/site-123/device-456/bulk',
        Buffer.from(JSON.stringify(pointBulkPayload)),
        { properties: {} }
      )

      // Verify point_bulk message was received
      expect(pointBulkMessages).toHaveLength(1)
      expect(pointBulkMessages[0]).toEqual(pointBulkPayload)

      subscription.unsubscribe()
    })
  })
})
