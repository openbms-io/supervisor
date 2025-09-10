import {
  DataNode,
  NodeCategory,
  NodeDirection,
  BacnetConfig,
  BacnetInputOutput,
  generateInstanceId,
} from '@/types/infrastructure'
import { BacnetProperties } from '@/types/bacnet-properties'

export class BinaryInputNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'binary-input' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  readonly discoveredProperties: BacnetProperties
  readonly name: string
  readonly position?: { x: number; y: number }

  // From DataNode
  readonly id: string
  readonly type = 'binary-input' as const
  readonly category = NodeCategory.BACNET
  readonly label: string
  readonly direction = NodeDirection.OUTPUT

  constructor(config: BacnetConfig) {
    // Copy all BacnetConfig properties
    this.pointId = config.pointId
    this.objectId = config.objectId
    this.supervisorId = config.supervisorId
    this.controllerId = config.controllerId
    this.discoveredProperties = Object.freeze({
      ...config.discoveredProperties,
    })
    this.name = config.name
    this.position = config.position

    // DataNode properties
    this.id = generateInstanceId() // Generate unique UUID for each instance
    this.label = config.name
  }

  canConnectWith(target: DataNode): boolean {
    return target.direction !== NodeDirection.OUTPUT
  }
}
