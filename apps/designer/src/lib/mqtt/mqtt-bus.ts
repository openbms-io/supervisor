import {
  BehaviorSubject,
  Observable,
  ReplaySubject,
  Subject,
  filter,
  map,
  shareReplay,
  take,
  timeout,
  throwError,
} from 'rxjs'
import mqtt from 'mqtt'
import type { MqttClient } from 'mqtt'
import { v4 as uuidv4 } from 'uuid'
import {
  getAllTopics,
  type AllTopics,
  type TopicParams,
  CommandNameEnum,
  type PointBulkPayload,
  type ControllerPoint,
} from 'mqtt-topics'

export type ConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'error'

export interface MqttMessage<T = unknown> {
  topic: string
  payload: T
  correlationId?: string
  responseTopic?: string
}

export interface SupervisorConfig {
  organizationId: string
  siteId: string
  iotDeviceId: string
}

class MqttBusCore {
  private client?: MqttClient
  private topics: AllTopics
  private messages$ = new Subject<MqttMessage>()
  private connection$ = new BehaviorSubject<ConnectionStatus>('disconnected')
  private heartbeat$ = new ReplaySubject<unknown>(1)
  private pointBulk$ = new Subject<PointBulkPayload>()

  private config: SupervisorConfig

  readonly connectionStatus$: Observable<ConnectionStatus> =
    this.connection$.asObservable()
  readonly heartbeatStream$: Observable<unknown> =
    this.heartbeat$.asObservable()
  readonly pointBulkStream$: Observable<PointBulkPayload> =
    this.pointBulk$.pipe(shareReplay({ bufferSize: 1, refCount: true }))

  constructor(config: SupervisorConfig) {
    this.config = config
    this.topics = this.buildTopics({ config })
    this.connect()
  }

  dispose(): void {
    this.client?.end(true)
    this.client = undefined

    this.messages$.complete()
    this.connection$.complete()
    this.heartbeat$.complete()
    this.pointBulk$.complete()
  }

  private buildTopics({ config }: { config: SupervisorConfig }): AllTopics {
    const params: TopicParams = {
      organization_id: config.organizationId,
      site_id: config.siteId,
      iot_device_id: config.iotDeviceId,
    }
    return getAllTopics({ params })
  }

  private connect(): void {
    if (!this.config || !this.topics) return

    const isBrowser = typeof window !== 'undefined'
    const allowNode = !isBrowser && process?.env?.MQTT_ENABLE_SERVER === '1'
    if (!isBrowser && !allowNode) return

    const url = isBrowser
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${
          window.location.host
        }/mqtt`
      : (process?.env?.MQTT_URL as string) ?? ''

    if (!url) {
      throw new Error('MQTT_URL env required for Node runtime')
    }

    this.connection$.next('connecting')

    this.client = mqtt.connect(url, {
      clientId: `designer_${this.config.iotDeviceId}_${Date.now()}`,
      reconnectPeriod: 5000,
      connectTimeout: 30000,
      protocolVersion: 5,
      clean: true,
    })

    this.client.on('connect', () => {
      this.connection$.next('connected')
      this.subscribeCoreTopics()
    })

    this.client.on('message', (topic, payload, packet) => {
      try {
        const correlationData = packet.properties?.correlationData
        const responseTopic = packet.properties?.responseTopic
        const msg: MqttMessage = {
          topic,
          payload: JSON.parse(payload.toString()),
          correlationId: correlationData
            ? correlationData.toString()
            : undefined,
          responseTopic: responseTopic ? responseTopic.toString() : undefined,
        }
        this.messages$.next(msg)
        this.routeToDomainStreams(msg)
      } catch (e) {
        console.error('MQTT parse error', e)
      }
    })

    this.client.on('error', (err) => {
      console.error('MQTT error', err)
      this.connection$.next('error')
    })

    this.client.on('close', () => {
      this.connection$.next('disconnected')
    })
  }

  private subscribeCoreTopics(): void {
    if (!this.client || !this.topics) return
    const { status, data, command } = this.topics

    this.client.subscribe(status.heartbeat.topic, {
      qos: status.heartbeat.qos as 0 | 1 | 2,
    })
    this.client.subscribe(data.point_bulk.topic, {
      qos: data.point_bulk.qos as 0 | 1 | 2,
    })

    for (const key of Object.keys(command) as Array<
      keyof AllTopics['command']
    >) {
      const resp = command[key]?.response
      if (resp?.topic) {
        this.client.subscribe(resp.topic, { qos: resp.qos as 0 | 1 | 2 })
      }
    }
  }

  private routeToDomainStreams(msg: MqttMessage): void {
    if (!this.topics) return
    const { status, data } = this.topics
    if (msg.topic === status.heartbeat.topic) {
      this.heartbeat$.next(msg.payload)
    } else if (msg.topic === data.point_bulk.topic) {
      this.pointBulk$.next(msg.payload as PointBulkPayload)
    }
  }

  streamForPoint(ids: {
    controllerId: string
    pointId: string
  }): Observable<ControllerPoint> {
    if (!ids.controllerId || !ids.pointId) {
      return throwError(
        () =>
          new Error(
            `Invalid point IDs: controllerId=${ids.controllerId}, pointId=${ids.pointId}`
          )
      )
    }

    const fromBulk$ = this.pointBulkStream$.pipe(
      map((bulk) => {
        const point = bulk.points?.find(
          (p) =>
            p.controller_id === ids.controllerId &&
            p.iot_device_point_id === ids.pointId
        )
        if (!point) {
          console.warn(
            `Point ${ids.pointId} not found in bulk message for controller ${ids.controllerId}`
          )
        }
        return point
      }),
      filter((point): point is ControllerPoint => !!point)
    )
    return fromBulk$.pipe(shareReplay({ bufferSize: 1, refCount: true }))
  }

  request<T = unknown>(
    command: CommandNameEnum,
    payload: unknown,
    timeoutMs = 30000
  ): Observable<T> {
    if (!this.client || !this.client.connected || !this.topics) {
      throw new Error('MQTT not connected')
    }
    const correlationId = uuidv4()
    const cmd = this.topics.command[command]
    if (!cmd) throw new Error(`Unknown command ${command}`)
    const req = cmd.request
    const res = cmd.response

    const response$ = this.messages$.pipe(
      filter((m) => m.topic === res.topic && m.correlationId === correlationId),
      map((m) => m.payload as T),
      take(1),
      timeout({ each: timeoutMs })
    )

    this.client.publish(req.topic, JSON.stringify(payload), {
      qos: req.qos as 0 | 1 | 2,
      retain: req.retain,
      properties: {
        correlationData: Buffer.from(correlationId),
        responseTopic: res.topic,
      },
    })

    return response$
  }
}

export class MqttBusManager {
  private currentBus?: MqttBusCore

  start({ config }: { config: SupervisorConfig }): void {
    this.currentBus?.dispose()
    this.currentBus = new MqttBusCore(config)
  }

  stop(): void {
    this.currentBus?.dispose()
    this.currentBus = undefined
  }

  get connectionStatus$(): Observable<ConnectionStatus> {
    if (!this.currentBus) {
      throw new Error('MQTT not started. Call start() first.')
    }
    return this.currentBus.connectionStatus$
  }

  get heartbeatStream$(): Observable<unknown> {
    if (!this.currentBus) {
      throw new Error('MQTT not started. Call start() first.')
    }
    return this.currentBus.heartbeatStream$
  }

  get pointBulkStream$(): Observable<PointBulkPayload> {
    if (!this.currentBus) {
      throw new Error('MQTT not started. Call start() first.')
    }
    return this.currentBus.pointBulkStream$
  }

  streamForPoint(ids: {
    controllerId: string
    pointId: string
  }): Observable<ControllerPoint> {
    if (!this.currentBus) {
      throw new Error('MQTT not started. Call start() first.')
    }
    return this.currentBus.streamForPoint(ids)
  }

  request<T = unknown>(
    command: CommandNameEnum,
    payload: unknown,
    timeoutMs = 30000
  ): Observable<T> {
    if (!this.currentBus) {
      throw new Error('MQTT not started. Call start() first.')
    }
    return this.currentBus.request<T>(command, payload, timeoutMs)
  }
}

let _busManager: MqttBusManager | undefined
export function getMqttBus(): MqttBusManager {
  if (!_busManager) _busManager = new MqttBusManager()
  return _busManager
}
