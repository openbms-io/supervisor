import {
  DataNode,
  NodeCategory,
  NodeDirection,
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
  readonly direction = NodeDirection.BIDIRECTIONAL
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

  canConnectWith(target: DataNode): boolean {
    return target.direction !== NodeDirection.OUTPUT
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
    const handles: BacnetOutputHandle[] = []
    for (const [property, value] of Object.entries(this.discoveredProperties)) {
      if (value !== undefined) {
        const metadata = getPropertyMetadata(
          this.objectType,
          property as BacnetOutputHandle
        )
        if (metadata?.readable) {
          handles.push(property as BacnetOutputHandle)
        }
      }
    }
    return handles
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
    const inputHandles = this.getInputHandles()

    if (inputHandles.includes(handle)) {
      // Write to a writable property
      console.log(
        `🟢 [${this.id}] BinaryInput received write to ${handle}:`,
        message.payload,
        `from ${fromNodeId}`
      )

      // Update the property value locally for UI updates
      // NOTE: Currently focusing on top-level properties only. Nested properties are not spread correctly.
      this.discoveredProperties = {
        ...this.discoveredProperties,
        [handle]: message.payload,
      }

      // Send the updated value downstream
      await this.send(
        {
          payload: message.payload,
          _msgid: uuidv4(),
          timestamp: Date.now(),
        },
        handle
      )
    } else {
      // Trigger - send all readable property values
      console.log(`🟢 [${this.id}] BinaryInput triggered from ${fromNodeId}`)

      const outputHandles = this.getOutputHandles()
      for (const propertyHandle of outputHandles) {
        const currentValue = this.discoveredProperties[propertyHandle]
        if (currentValue !== undefined) {
          await this.send(
            {
              payload: currentValue,
              _msgid: uuidv4(),
              timestamp: Date.now(),
            },
            propertyHandle
          )
        }
      }
    }
  }
}
