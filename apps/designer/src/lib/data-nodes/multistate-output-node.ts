import {
  DataNode,
  NodeCategory,
  NodeType,
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
import { makeSerializable } from '@/lib/workflow/serialization-utils'
import { prepareMultistateProperties } from './bacnet-utils'

export class MultistateOutputNode implements BacnetInputOutput {
  // From BacnetConfig
  readonly pointId: string
  readonly objectType = 'multistate-output' as const
  readonly objectId: number
  readonly supervisorId: string
  readonly controllerId: string
  discoveredProperties: BacnetProperties
  readonly name: string
  readonly position?: { x: number; y: number }

  // From DataNode
  readonly id: string
  readonly type = NodeType.MULTISTATE_OUTPUT
  readonly category = NodeCategory.BACNET
  readonly label: string
  readonly direction = NodeDirection.INPUT
  private sendCallback?: SendCallback<BacnetOutputHandle>

  constructor(config: BacnetConfig, id?: string) {
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
    this.id = id ?? generateInstanceId() // Generate unique UUID for each instance
    this.label = config.name
  }

  canConnectWith(source: DataNode): boolean {
    // Multistate outputs accept input from logic/calculation nodes
    return source.direction !== NodeDirection.INPUT
  }

  toSerializable() {
    const metadata: BacnetConfig = {
      pointId: this.pointId,
      objectType: this.objectType,
      objectId: this.objectId,
      supervisorId: this.supervisorId,
      controllerId: this.controllerId,
      name: this.name,
      discoveredProperties: this.discoveredProperties,
      position: this.position,
    }
    return makeSerializable<
      BacnetConfig,
      NodeType.MULTISTATE_OUTPUT,
      NodeCategory.BACNET
    >({
      id: this.id,
      type: this.type,
      category: this.category,
      label: this.label,
      metadata,
    })
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
      `🔢 [${this.id}] MultistateOutput received write to ${handle}:`,
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
      `🔢 [${this.id}] Would write ${handle} = ${message.payload} to device ${this.objectId}`
    )
  }
}
