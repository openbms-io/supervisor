import {
  DataNode,
  LogicNode,
  LogicOutputHandle,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export type ValueType = 'number' | 'boolean' | 'string'

// Export the metadata interface
export interface ConstantNodeMetadata {
  value: number | boolean | string
  valueType: ValueType
}

export class ConstantNode implements LogicNode<never, LogicOutputHandle> {
  readonly id: string
  readonly type = 'constant' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.OUTPUT

  private _metadata: ConstantNodeMetadata
  private sendCallback?: SendCallback<LogicOutputHandle>

  get metadata(): ConstantNodeMetadata {
    return this._metadata
  }

  // Public getter for UI access - returns the constant value
  get computedValue(): ComputeValue | undefined {
    const value = this._metadata.value
    return typeof value === 'number' || typeof value === 'boolean'
      ? value
      : undefined
  }

  constructor(
    label: string,
    value: number | boolean | string = 0,
    valueType: ValueType = 'number'
  ) {
    this.id = generateInstanceId()
    this.label = label
    this._metadata = { value, valueType }
  }

  getValue(): ComputeValue | undefined {
    const value = this._metadata.value
    return typeof value === 'number' || typeof value === 'boolean'
      ? value
      : undefined
  }

  // Constants don't reset - they maintain their value
  // No reset() method needed

  canConnectWith(target: DataNode): boolean {
    // Constants can connect to anything that accepts input
    // (anything except pure output nodes)
    return target.direction !== NodeDirection.OUTPUT
  }

  // Constants have no inputs
  getInputHandles(): readonly never[] {
    return [] as const
  }

  getOutputHandles(): readonly LogicOutputHandle[] {
    return ['output'] as const
  }

  setValue(value: number | boolean | string): void {
    this._metadata = { ...this._metadata, value }
  }

  setValueType(valueType: ValueType): void {
    let newValue: number | boolean | string
    switch (valueType) {
      case 'number':
        newValue = 0
        break
      case 'boolean':
        newValue = false
        break
      case 'string':
        newValue = ''
        break
    }

    this._metadata = { valueType, value: newValue }
  }

  // Message passing API implementation
  setSendCallback(callback: SendCallback<LogicOutputHandle>): void {
    this.sendCallback = callback
  }

  private async send(
    message: Message,
    handle: LogicOutputHandle
  ): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _message: Message,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _handle: never,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _fromNodeId: string
  ): Promise<void> {
    // Source node - when triggered, send the constant value
    await this.trigger()
  }

  // Internal API - called by DataGraph execution system
  async trigger(): Promise<void> {
    const value = this.getValue()
    if (value !== undefined) {
      console.log(`🔢 [${this.id}] Triggered, sending constant value:`, value)
      await this.send(
        {
          payload: value,
          _msgid: uuidv4(),
          timestamp: Date.now(),
          metadata: { source: this.id, type: this.type },
        },
        'output'
      )
    }
  }
}
