import {
  DataNode,
  BacnetConfig,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'

// Example BACnet output node (e.g., damper actuator)
export class AnalogOutputNode implements DataNode {
  readonly id: string
  readonly type = 'analog-output' as const
  readonly label: string
  readonly direction = NodeDirection.INPUT
  readonly metadata: BacnetConfig

  constructor(config: BacnetConfig) {
    this.id = generateInstanceId()
    this.label = config.name
    this.metadata = config
  }

  canConnectWith(): boolean {
    // Output nodes are terminal - no outgoing connections
    return false
  }
}
