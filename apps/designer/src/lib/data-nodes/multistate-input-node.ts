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
import { convertToComputeValue } from './bacnet-utils'
import { prepareMultistateProperties } from './bacnet-utils'

export class MultistateInputNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'multistate-input' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  discoveredProperties: BacnetProperties
  readonly name: string
  readonly position?: { x: number; y: number }

  // From DataNode
  readonly id: string
  readonly type = 'multistate-input' as const
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

    // Use utility to prepare properties with 1-based indexing
    this.discoveredProperties = prepareMultistateProperties(
      config.discoveredProperties
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
        `🔢 [${this.id}] MultistateInput received write to ${handle}:`,
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
      console.log(
        `🔢 [${this.id}] MultistateInput triggered from ${fromNodeId}`
      )

      const outputHandles = this.getOutputHandles()
      for (const propertyHandle of outputHandles) {
        const currentValue = this.discoveredProperties[propertyHandle]
        if (currentValue !== undefined) {
          await this.send(
            {
              payload: convertToComputeValue(currentValue) || 0,
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
