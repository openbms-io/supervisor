import {
  DataNode,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'

// Example command node for writing setpoints
export class WriteSetpointNode implements DataNode {
  readonly id: string
  readonly type = 'write-setpoint' as const
  readonly category = NodeCategory.COMMAND
  readonly label: string
  readonly direction = NodeDirection.INPUT
  readonly metadata: {
    targetPointId?: string
    propertyName?: string // e.g., 'presentValue', 'setpoint'
  }

  constructor(label: string, targetPointId?: string, propertyName?: string) {
    this.id = generateInstanceId()
    this.label = label
    this.metadata = { targetPointId, propertyName }
  }

  canConnectWith(): boolean {
    // Command nodes are terminal - no outgoing connections
    return false
  }
}
