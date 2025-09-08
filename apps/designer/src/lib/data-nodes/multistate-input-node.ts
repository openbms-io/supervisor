import {
  DataNode,
  NodeCategory,
  NodeDirection,
  BacnetConfig,
  BacnetInputOutput,
  generateInstanceId,
} from '@/types/infrastructure'
import { BacnetProperties } from '@/types/bacnet-properties'
import { prepareMultistateProperties } from './bacnet-utils'

export class MultistateInputNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'multistate-input' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  readonly discoveredProperties: BacnetProperties
  readonly name: string
  readonly position?: { x: number; y: number }

  // From DataNode
  readonly id: string
  readonly type = 'multistate-input' as const
  readonly category = NodeCategory.BACNET
  readonly label: string
  readonly direction = NodeDirection.OUTPUT

  constructor(config: BacnetConfig) {
    // Copy all BacnetConfig properties
    this.pointId = config.pointId
    this.objectId = config.objectId
    this.supervisorId = config.supervisorId
    this.controllerId = config.controllerId

    // Use utility to prepare properties with 1-based indexing
    this.discoveredProperties = Object.freeze(
      prepareMultistateProperties(config.discoveredProperties)
    )

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
