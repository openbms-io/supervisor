import {
  CommandNode,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
  ComputeValue,
  DataNode,
  CommandInputHandle,
  CommandOutputHandle,
} from '@/types/infrastructure'

export class WriteSetpointNode implements CommandNode {
  readonly id: string
  readonly type = 'write-setpoint' as const
  readonly category = NodeCategory.COMMAND
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL

  receivedValue?: ComputeValue
  priority: number = 8 // Default BACnet priority
  writeMode: 'normal' | 'override' | 'release' = 'normal'

  constructor(label: string, priority: number = 8) {
    this.id = generateInstanceId()
    this.label = label
    this.priority = Math.max(1, Math.min(16, priority)) // Clamp 1-16
  }

  canConnectWith(other: DataNode): boolean {
    // Output can connect to BACnet nodes or chain to other commands
    return (
      other.category === NodeCategory.BACNET ||
      other.category === NodeCategory.COMMAND
    )
  }

  getInputHandles(): readonly CommandInputHandle[] {
    return ['setpoint'] as const
  }

  getOutputHandles(): readonly CommandOutputHandle[] {
    return ['output'] as const
  }
}
