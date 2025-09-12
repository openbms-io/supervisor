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
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export class WriteSetpointNode implements CommandNode {
  readonly id: string
  readonly type = 'write-setpoint' as const
  readonly category = NodeCategory.COMMAND
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL

  receivedValue?: ComputeValue
  priority: number = 8 // Default BACnet priority
  writeMode: 'normal' | 'override' | 'release' = 'normal'
  private sendCallback?: SendCallback<CommandOutputHandle>

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

  // Message passing API implementation
  setSendCallback(callback: SendCallback<CommandOutputHandle>): void {
    this.sendCallback = callback
  }

  private async send(
    message: Message,
    handle: CommandOutputHandle
  ): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    message: Message,
    handle: CommandInputHandle,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `📝 [${this.id}] WriteSetpoint received on ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    // Store the setpoint value
    this.receivedValue = message.payload

    console.log(
      `📝 [${this.id}] Writing setpoint:`,
      this.receivedValue,
      `priority: ${this.priority}`
    )

    // Forward the setpoint value to connected BACnet nodes
    await this.send(
      {
        payload: this.receivedValue,
        _msgid: uuidv4(),
        timestamp: Date.now(),
        metadata: {
          source: this.id,
          type: 'setpoint',
          priority: this.priority,
          writeMode: this.writeMode,
        },
      },
      'output'
    )
  }
}
