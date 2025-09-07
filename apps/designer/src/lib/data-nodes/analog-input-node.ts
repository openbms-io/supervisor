import {
  DataNode,
  BacnetConfig,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'

// Example BACnet input node (e.g., temperature sensor)
export class AnalogInputNode implements DataNode {
  readonly id: string
  readonly type = 'analog-input' as const
  readonly label: string
  readonly direction = NodeDirection.OUTPUT
  readonly metadata: BacnetConfig

  constructor(config: BacnetConfig) {
    this.id = generateInstanceId()
    this.label = config.name
    this.metadata = config
  }

  canConnectWith(target: DataNode): boolean {
    // Inputs can connect to logic nodes or output nodes
    // Cannot connect to other input nodes
    return target.direction !== NodeDirection.OUTPUT
  }
}
