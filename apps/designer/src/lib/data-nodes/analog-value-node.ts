import {
  DataNode,
  NodeCategory,
  NodeDirection,
  BacnetConfig,
  BacnetInputOutput,
} from '@/types/infrastructure'

export class AnalogValueNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'analog-value' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  readonly presentValue: number | boolean | string
  readonly units?: string
  readonly description: string
  readonly reliability: string
  readonly statusFlags: {
    inAlarm: boolean
    fault: boolean
    overridden: boolean
    outOfService: boolean
  }
  readonly name: string
  readonly position?: { x: number; y: number }
  readonly minValue?: number
  readonly maxValue?: number

  // From DataNode
  readonly id: string
  readonly type = 'analog-value' as const
  readonly category = NodeCategory.BACNET
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL

  constructor(config: BacnetConfig) {
    // Copy all BacnetConfig properties
    this.pointId = config.pointId
    this.objectId = config.objectId
    this.supervisorId = config.supervisorId
    this.controllerId = config.controllerId
    this.presentValue = config.presentValue
    this.units = config.units
    this.description = config.description
    this.reliability = config.reliability
    this.statusFlags = config.statusFlags
    this.name = config.name
    this.position = config.position
    this.minValue = config.minValue
    this.maxValue = config.maxValue

    // DataNode properties
    this.id = config.pointId
    this.label = config.name
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  canConnectWith(target: DataNode): boolean {
    // Value nodes can connect bidirectionally
    return true
  }
}
