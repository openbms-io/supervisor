import {
  DataNode,
  NodeCategory,
  NodeDirection,
  BacnetConfig,
  BacnetInputOutput,
  generateInstanceId,
} from '@/types/infrastructure'
import { BacnetProperties } from '@/types/bacnet-properties'

export class BinaryValueNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'binary-value' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  readonly discoveredProperties: BacnetProperties
  readonly name: string
  readonly position?: { x: number; y: number }

  // From DataNode
  readonly id: string
  readonly type = 'binary-value' as const
  readonly category = NodeCategory.BACNET
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL

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

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  canConnectWith(target: DataNode): boolean {
    // Value nodes can connect bidirectionally
    return true
  }
}
