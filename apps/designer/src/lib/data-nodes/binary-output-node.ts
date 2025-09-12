import {
  NodeCategory,
  NodeDirection,
  DataNode,
  BacnetConfig,
  BacnetInputOutput,
  generateInstanceId,
  BacnetInputHandle,
  BacnetOutputHandle,
} from '@/types/infrastructure'
import {
  BacnetProperties,
  getPropertyMetadata,
} from '@/types/bacnet-properties'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export class BinaryOutputNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'binary-output' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  readonly discoveredProperties: BacnetProperties
  readonly name: string
  readonly position?: { x: number; y: number }

  // From DataNode
  readonly id: string
  readonly type = 'binary-output' as const
  readonly category = NodeCategory.BACNET
  readonly label: string
  readonly direction = NodeDirection.INPUT
  private sendCallback?: SendCallback<BacnetOutputHandle>

  constructor(config: BacnetConfig) {
    // Copy all BacnetConfig properties
    this.pointId = config.pointId
    this.objectId = config.objectId
    this.supervisorId = config.supervisorId
    this.controllerId = config.controllerId
    this.discoveredProperties = {
      ...config.discoveredProperties,
    }
    this.name = config.name
    this.position = config.position

    // DataNode properties
    this.id = generateInstanceId() // Generate unique UUID for each instance
    this.label = config.name
  }

  canConnectWith(source: DataNode): boolean {
    // Binary outputs accept input from logic/calculation nodes
    return source.direction !== NodeDirection.INPUT
  }

  getInputHandles(): readonly BacnetInputHandle[] {
    const handles: BacnetInputHandle[] = []
    for (const [property, value] of Object.entries(this.discoveredProperties)) {
      if (value !== undefined) {
        const metadata = getPropertyMetadata(
          this.objectType,
          property as BacnetInputHandle
        )
        if (metadata?.writable) {
          handles.push(property as BacnetInputHandle)
        }
      }
    }
    return handles
  }

  getOutputHandles(): readonly BacnetOutputHandle[] {
    return [] as const // Output nodes are sinks
  }

  // Message passing API implementation
  setSendCallback(callback: SendCallback<BacnetOutputHandle>): void {
    this.sendCallback = callback
  }

  private async send(
    message: Message,
    handle: BacnetOutputHandle
  ): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    message: Message,
    handle: BacnetInputHandle,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `🟢 [${this.id}] BinaryOutput received write to ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    // Update the property value locally
    // NOTE: Currently focusing on top-level properties only. Nested properties are not spread correctly.
    this.discoveredProperties = {
      ...this.discoveredProperties,
      [handle]: message.payload,
    }

    console.log(
      `🟢 [${this.id}] Would write ${handle} = ${message.payload} to device ${this.objectId}`
    )
  }
}
