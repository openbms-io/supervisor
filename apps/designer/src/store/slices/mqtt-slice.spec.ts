import { create } from 'zustand'
import { Subject } from 'rxjs'
import { MQTTSlice, createMQTTSlice, HeartbeatPayload } from './mqtt-slice'
import { getMqttBus } from '@/lib/mqtt/mqtt-bus'
import type { ConnectionStatus } from '@/lib/mqtt/mqtt-bus'
import { CommandNameEnum } from 'mqtt-topics'

jest.mock('@/lib/mqtt/mqtt-bus')

describe('MQTTSlice', () => {
  let mockBus: {
    start: jest.Mock
    stop: jest.Mock
    connectionStatus$: Subject<ConnectionStatus>
    heartbeatStream$: Subject<HeartbeatPayload>
    request: jest.Mock
  }

  beforeEach(() => {
    mockBus = {
      start: jest.fn(),
      stop: jest.fn(),
      connectionStatus$: new Subject(),
      heartbeatStream$: new Subject(),
      request: jest.fn(),
    }
    ;(getMqttBus as jest.Mock).mockReturnValue(mockBus)
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Initial State', () => {
    it('should initialize with connectionStatus disconnected', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      expect(store.getState().connectionStatus).toBe('disconnected')
    })

    it('should initialize with brokerHealth status unknown', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      expect(store.getState().brokerHealth.status).toBe('unknown')
    })

    it('should have no lastError initially', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      expect(store.getState().lastError).toBeUndefined()
    })
  })

  describe('startMqtt', () => {
    it('should call bus.start with correct config', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      expect(mockBus.start).toHaveBeenCalledWith({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })
    })

    it('should update connectionStatus when bus emits connecting', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.connectionStatus$.next('connecting')
      expect(store.getState().connectionStatus).toBe('connecting')
    })

    it('should update connectionStatus when bus emits connected', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.connectionStatus$.next('connected')
      expect(store.getState().connectionStatus).toBe('connected')
    })

    it('should set broker health to healthy when heartbeat received', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      const heartbeat: HeartbeatPayload = {
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

      mockBus.heartbeatStream$.next(heartbeat)

      expect(store.getState().brokerHealth.status).toBe('healthy')
    })

    it('should store heartbeat payload in lastHeartbeat', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      const heartbeat: HeartbeatPayload = {
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

      mockBus.heartbeatStream$.next(heartbeat)

      expect(store.getState().brokerHealth.lastHeartbeat).toEqual(heartbeat)
    })

    it('should update lastHeartbeatTimestamp to current time', () => {
      const now = Date.now()
      jest.spyOn(Date, 'now').mockReturnValue(now)

      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      const heartbeat: HeartbeatPayload = {
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
        timestamp: now / 1000,
        organization_id: 'org_test',
        site_id: 'site-123',
        iot_device_id: 'device-456',
      }

      mockBus.heartbeatStream$.next(heartbeat)

      expect(store.getState().brokerHealth.lastHeartbeatTimestamp).toBe(now)
    })

    it('should set broker status to unhealthy on heartbeat stream error', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.heartbeatStream$.error(new Error('Stream error'))

      expect(store.getState().brokerHealth.status).toBe('unhealthy')
    })

    it('should set lastError when heartbeat stream errors', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.heartbeatStream$.error(new Error('Connection lost'))

      expect(store.getState().lastError).toBe('Error: Connection lost')
    })
  })

  describe('Heartbeat Watchdog', () => {
    it('should mark broker unhealthy after 60s silence', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      const heartbeat: HeartbeatPayload = {
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

      mockBus.heartbeatStream$.next(heartbeat)
      expect(store.getState().brokerHealth.status).toBe('healthy')

      jest.advanceTimersByTime(65_000)

      expect(store.getState().brokerHealth.status).toBe('unhealthy')
    })

    it('should remain healthy when heartbeats continue within 60s', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      for (let i = 0; i < 5; i++) {
        const heartbeat: HeartbeatPayload = {
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

        mockBus.heartbeatStream$.next(heartbeat)
        jest.advanceTimersByTime(30_000)
      }

      expect(store.getState().brokerHealth.status).toBe('healthy')
    })

    it('should not change status if already unhealthy and still silent', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      const heartbeat: HeartbeatPayload = {
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

      mockBus.heartbeatStream$.next(heartbeat)
      jest.advanceTimersByTime(65_000)
      expect(store.getState().brokerHealth.status).toBe('unhealthy')

      jest.advanceTimersByTime(30_000)
      expect(store.getState().brokerHealth.status).toBe('unhealthy')
    })

    it('should handle missing lastHeartbeatTimestamp gracefully', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      jest.advanceTimersByTime(70_000)

      expect(store.getState().brokerHealth.status).toBe('unknown')
    })
  })

  describe('stopMqtt', () => {
    it('should call bus.stop', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      store.getState().stopMqtt()

      expect(mockBus.stop).toHaveBeenCalled()
    })

    it('should reset connectionStatus to disconnected', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.connectionStatus$.next('connected')
      expect(store.getState().connectionStatus).toBe('connected')

      store.getState().stopMqtt()

      expect(store.getState().connectionStatus).toBe('disconnected')
    })

    it('should reset brokerHealth status to unknown', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      const heartbeat: HeartbeatPayload = {
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

      mockBus.heartbeatStream$.next(heartbeat)
      expect(store.getState().brokerHealth.status).toBe('healthy')

      store.getState().stopMqtt()

      expect(store.getState().brokerHealth.status).toBe('unknown')
    })

    it('should clear lastError', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.heartbeatStream$.error(new Error('Test error'))
      expect(store.getState().lastError).toBeDefined()

      store.getState().stopMqtt()

      expect(store.getState().lastError).toBeUndefined()
    })

    it('should unsubscribe from all RxJS streams', () => {
      const store = create<MQTTSlice>()(createMQTTSlice)
      store.getState().startMqtt({
        organizationId: 'org_test',
        siteId: 'site-123',
        iotDeviceId: 'device-456',
      })

      mockBus.connectionStatus$.next('connected')
      expect(store.getState().connectionStatus).toBe('connected')

      store.getState().stopMqtt()

      mockBus.connectionStatus$.next('connecting')
      expect(store.getState().connectionStatus).toBe('disconnected')
    })
  })

  describe('sendCommand', () => {
    it('should call bus.request with correct enum and payload', async () => {
      const mockObservable = {
        toPromise: jest.fn().mockResolvedValue({ success: true }),
      }
      mockBus.request.mockReturnValue(mockObservable)

      const store = create<MQTTSlice>()(createMQTTSlice)
      const payload = { test: 'data' }

      const result = await store.getState().sendCommand({
        command: CommandNameEnum.GET_CONFIG,
        payload,
      })

      expect(mockBus.request).toHaveBeenCalledWith(
        CommandNameEnum.GET_CONFIG,
        payload
      )
      expect(result).toEqual({ success: true })
    })

    it('should handle request timeout', async () => {
      const mockObservable = {
        toPromise: jest.fn().mockRejectedValue(new Error('Timeout')),
      }
      mockBus.request.mockReturnValue(mockObservable)

      const store = create<MQTTSlice>()(createMQTTSlice)

      await expect(
        store.getState().sendCommand({
          command: CommandNameEnum.REBOOT,
          payload: {},
        })
      ).rejects.toThrow('Timeout')
    })
  })
})
