import { StateCreator } from 'zustand'
import { Subject, interval } from 'rxjs'
import { takeUntil } from 'rxjs/operators'
import { getMqttBus } from '@/lib/mqtt/mqtt-bus'
import { CommandNameEnum } from 'mqtt-topics'

export interface HeartbeatPayload {
  cpu_usage_percent: number | null
  memory_usage_percent: number | null
  disk_usage_percent: number | null
  temperature_celsius: number | null
  uptime_seconds: number | null
  load_average: number | null
  monitoring_status: string | null
  mqtt_connection_status: string | null
  bacnet_connection_status: string | null
  bacnet_devices_connected: number | null
  bacnet_points_monitored: number | null
  timestamp: number
  organization_id: string
  site_id: string
  iot_device_id: string
}

export interface BrokerHealth {
  status: 'unknown' | 'healthy' | 'unhealthy'
  lastHeartbeat?: HeartbeatPayload
  lastHeartbeatTimestamp?: number
}

export interface MQTTSlice {
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  brokerHealth: BrokerHealth
  lastError?: string
  startMqtt: ({
    organizationId,
    siteId,
    iotDeviceId,
  }: {
    organizationId: string
    siteId: string
    iotDeviceId: string
  }) => void
  stopMqtt: () => void
  sendCommand: ({
    command,
    payload,
  }: {
    command: CommandNameEnum
    payload: unknown
  }) => Promise<unknown>
}

export const createMQTTSlice: StateCreator<MQTTSlice> = (set, get) => {
  let mqttStop$: Subject<void> | undefined

  const internalStop = () => {
    getMqttBus().stop()
    if (mqttStop$) {
      mqttStop$.next()
      mqttStop$.complete()
      mqttStop$ = undefined
    }
    set({
      connectionStatus: 'disconnected',
      brokerHealth: { status: 'unknown' },
      lastError: undefined,
    })
  }

  return {
    connectionStatus: 'disconnected',
    brokerHealth: { status: 'unknown' },

    startMqtt: ({ organizationId, siteId, iotDeviceId }) => {
      internalStop()
      const bus = getMqttBus()
      bus.start({
        config: {
          organizationId,
          siteId,
          iotDeviceId,
        },
      })

      mqttStop$ = new Subject<void>()

      bus.connectionStatus$.pipe(takeUntil(mqttStop$)).subscribe((s) => {
        set({ connectionStatus: s })
      })

      bus.heartbeatStream$.pipe(takeUntil(mqttStop$)).subscribe({
        next: (hb) =>
          set({
            brokerHealth: {
              status: 'healthy',
              lastHeartbeat: hb as HeartbeatPayload,
              lastHeartbeatTimestamp: Date.now(),
            },
          }),
        error: (e) =>
          set({
            brokerHealth: { ...get().brokerHealth, status: 'unhealthy' },
            lastError: String(e),
          }),
      })

      const HEARTBEAT_THRESHOLD_MS = 60_000
      interval(5_000)
        .pipe(takeUntil(mqttStop$))
        .subscribe(() => {
          const { brokerHealth } = get()
          console.log('heartbeat check', brokerHealth)

          if (!brokerHealth.lastHeartbeatTimestamp) return
          const silentFor = Date.now() - brokerHealth.lastHeartbeatTimestamp
          if (
            silentFor > HEARTBEAT_THRESHOLD_MS &&
            brokerHealth.status !== 'unhealthy'
          ) {
            set({ brokerHealth: { ...brokerHealth, status: 'unhealthy' } })
          } else if (
            silentFor <= HEARTBEAT_THRESHOLD_MS &&
            brokerHealth.status !== 'healthy'
          ) {
            set({ brokerHealth: { ...brokerHealth, status: 'healthy' } })
          }
        })
    },

    stopMqtt: () => {
      internalStop()
    },

    sendCommand: async ({
      command,
      payload,
    }: {
      command: CommandNameEnum
      payload: unknown
    }) => {
      const bus = getMqttBus()
      return bus.request(command, payload).toPromise()
    },
  }
}
