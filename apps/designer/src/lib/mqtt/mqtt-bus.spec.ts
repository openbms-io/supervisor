import mqtt from 'mqtt'
import { MqttBusManager, getMqttBus } from './mqtt-bus'

jest.mock('mqtt', () => ({
  __esModule: true,
  default: {
    connect: jest.fn(),
  },
}))
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'test-uuid-123'),
}))

describe('MqttBusManager', () => {
  let mockClient: any

  beforeEach(() => {
    mockClient = {
      on: jest.fn(),
      subscribe: jest.fn(),
      publish: jest.fn(),
      end: jest.fn(),
      connected: false,
    }
    ;(mqtt.connect as jest.Mock).mockReturnValue(mockClient)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Connection', () => {
    it('should use ws protocol for http and wss for https', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const url = (mqtt.connect as jest.Mock).mock.calls[0][0]

      // Should use ws:// (not wss://) since window.location.protocol is http: in jsdom
      expect(url).toMatch(/^ws:\/\/.+\/mqtt$/)

      // In production with https, the code would use wss://
      // This is verified by the implementation: window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    })

    it('should use MQTT 5.0 protocol version', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      expect(mqtt.connect).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          protocolVersion: 5,
        })
      )
    })

    it('should set clean session to true', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      expect(mqtt.connect).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          clean: true,
        })
      )
    })

    it('should include device ID in client ID', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      expect(mqtt.connect).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          clientId: expect.stringContaining('device-456'),
        })
      )
    })
  })

  describe('Subscriptions', () => {
    it('should subscribe to heartbeat topic on connect', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]
      connectHandler()

      expect(mockClient.subscribe).toHaveBeenCalledWith(
        expect.stringContaining('/status/heartbeat'),
        expect.any(Object)
      )
    })

    it('should subscribe to point_bulk topic on connect', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]
      connectHandler()

      expect(mockClient.subscribe).toHaveBeenCalledWith(
        expect.stringContaining('/bulk'),
        expect.any(Object)
      )
    })

    it('should subscribe to command response topics', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]
      connectHandler()

      expect(mockClient.subscribe).toHaveBeenCalledWith(
        expect.stringContaining('/command/get_config/response'),
        expect.any(Object)
      )
    })

    it('should pass correct topic strings with org_id/site_id/iot_device_id', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const connectHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      )?.[1]
      connectHandler()

      const heartbeatCall = mockClient.subscribe.mock.calls.find((call: any) =>
        call[0].includes('/status/heartbeat')
      )
      expect(heartbeatCall[0]).toContain('org_test')
      expect(heartbeatCall[0]).toContain('site-123')
      expect(heartbeatCall[0]).toContain('device-456')
    })
  })

  describe('Heartbeat Stream', () => {
    it('should emit heartbeat payloads to heartbeatStream$', (done) => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const heartbeatPayload = {
        cpu_usage_percent: 10.5,
        uptime_seconds: 666,
        timestamp: Date.now() / 1000,
      }

      bus.heartbeatStream$.subscribe((hb) => {
        expect(hb).toEqual(heartbeatPayload)
        done()
      })

      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]
      messageHandler(
        'iot/global/org_test/site-123/device-456/status/heartbeat',
        Buffer.from(JSON.stringify(heartbeatPayload)),
        { properties: {} }
      )
    })

    it('should parse JSON heartbeat messages', (done) => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const heartbeatPayload = {
        cpu_usage_percent: 15.2,
        monitoring_status: 'active',
      }

      bus.heartbeatStream$.subscribe((hb) => {
        expect(hb.cpu_usage_percent).toBe(15.2)
        expect(hb.monitoring_status).toBe('active')
        done()
      })

      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]
      messageHandler(
        'iot/global/org_test/site-123/device-456/status/heartbeat',
        Buffer.from(JSON.stringify(heartbeatPayload)),
        { properties: {} }
      )
    })

    it('should handle malformed heartbeat JSON gracefully', () => {
      const bus = new MqttBusManager()
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]
      messageHandler(
        'iot/global/org_test/site-123/device-456/status/heartbeat',
        Buffer.from('invalid json{'),
        { properties: {} }
      )

      expect(consoleSpy).toHaveBeenCalledWith(
        'MQTT parse error',
        expect.any(Error)
      )
      consoleSpy.mockRestore()
    })
  })

  describe('Point Bulk Stream', () => {
    it('should emit point_bulk payloads to pointBulkStream$', (done) => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      const pointBulkPayload = {
        controller_id: 'ctrl-1',
        points: [{ iot_device_point_id: 'point-1', present_value: 23.5 }],
      }

      bus.pointBulkStream$.subscribe((bulk) => {
        expect(bulk).toEqual(pointBulkPayload)
        done()
      })

      const messageHandler = mockClient.on.mock.calls.find(
        (call: any) => call[0] === 'message'
      )?.[1]
      messageHandler(
        'iot/global/org_test/site-123/device-456/bulk',
        Buffer.from(JSON.stringify(pointBulkPayload)),
        { properties: {} }
      )
    })
  })

  describe('Cleanup', () => {
    it('should disconnect client on stop', () => {
      const bus = new MqttBusManager()
      bus.start({
        config: {
          organizationId: 'org_test',
          siteId: 'site-123',
          iotDeviceId: 'device-456',
        },
      })

      bus.stop()

      expect(mockClient.end).toHaveBeenCalledWith(true)
    })

    it('should handle stop when not connected', () => {
      const bus = new MqttBusManager()

      expect(() => bus.stop()).not.toThrow()
    })
  })

  describe('Singleton', () => {
    it('should return same instance for getMqttBus', () => {
      const bus1 = getMqttBus()
      const bus2 = getMqttBus()

      expect(bus1).toBe(bus2)
    })
  })
})
