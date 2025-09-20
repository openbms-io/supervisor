import {
  ControlFlowNode,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  DataNode,
  SwitchInputHandle,
  SwitchOutputHandle,
  generateInstanceId,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export class SwitchNode
  implements ControlFlowNode<SwitchInputHandle, SwitchOutputHandle>
{
  readonly id: string
  // REMOVED: pointId - not needed for non-BACnet nodes
  readonly category = NodeCategory.CONTROL_FLOW
  readonly type = 'switch'
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata = undefined

  label: string

  // Private internal state
  private _inputValue?: ComputeValue
  private _condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
  private _threshold: number
  private sendCallback?: SendCallback<SwitchOutputHandle>

  // Public getters for UI access
  get inputValue(): ComputeValue | undefined {
    return this._inputValue
  }

  get computedValue(): ComputeValue | undefined {
    return this._inputValue // Pass through the input
  }

  get condition(): 'gt' | 'lt' | 'eq' | 'gte' | 'lte' {
    return this._condition
  }

  get threshold(): number {
    return this._threshold
  }

  // Encapsulated setters
  setCondition(condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'): void {
    this._condition = condition
  }

  setThreshold(threshold: number): void {
    this._threshold = threshold
  }

  // Optional custom labels for UI display
  activeLabel: string
  inactiveLabel: string

  constructor(
    label: string,
    condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte' = 'gt',
    threshold: number = 0,
    activeLabel?: string,
    inactiveLabel?: string,
    id?: string
  ) {
    this.id = id || generateInstanceId()
    this.label = label
    this._condition = condition
    this._threshold = threshold

    // Set display labels based on condition type
    this.activeLabel = activeLabel || this.getDefaultActiveLabel()
    this.inactiveLabel = inactiveLabel || this.getDefaultInactiveLabel()
  }

  private getDefaultActiveLabel(): string {
    switch (this._condition) {
      case 'gt':
      case 'gte':
        return 'Above Threshold'
      case 'lt':
      case 'lte':
        return 'Below Threshold'
      case 'eq':
        return 'At Setpoint'
      default:
        return 'Active'
    }
  }

  private getDefaultInactiveLabel(): string {
    switch (this._condition) {
      case 'gt':
      case 'gte':
        return 'Below Threshold'
      case 'lt':
      case 'lte':
        return 'Above Threshold'
      case 'eq':
        return 'Not at Setpoint'
      default:
        return 'Inactive'
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  canConnectWith(_other: DataNode): boolean {
    return true // Switch can connect to anything
  }

  getInputHandles(): readonly SwitchInputHandle[] {
    return ['input'] as const
  }

  getOutputHandles(): readonly SwitchOutputHandle[] {
    return ['active', 'inactive'] as const
  }

  getValue(): ComputeValue | undefined {
    return this._inputValue
  }

  reset(): void {
    this._inputValue = undefined
  }

  private evaluate(): boolean {
    if (this._inputValue === undefined) return false

    const value = Number(this._inputValue)
    const thresh = Number(this._threshold)

    switch (this._condition) {
      case 'gt':
        return value > thresh
      case 'gte':
        return value >= thresh
      case 'lt':
        return value < thresh
      case 'lte':
        return value <= thresh
      case 'eq':
        return value === thresh
      default:
        return false
    }
  }

  getActiveOutputHandles(): readonly SwitchOutputHandle[] {
    const isActive = this.evaluate()
    const handle: SwitchOutputHandle = isActive ? 'active' : 'inactive'
    return [handle] as const
  }

  // Message passing API implementation
  setSendCallback(callback: SendCallback<SwitchOutputHandle>): void {
    this.sendCallback = callback
  }

  private async send(
    message: Message,
    handle: SwitchOutputHandle
  ): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    message: Message,
    handle: SwitchInputHandle,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `🔀 [${this.id}] Switch received on ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    // Set the input value and evaluate condition
    this._inputValue = message.payload
    const isActive = this.evaluate()

    // Send to the appropriate output
    const outputHandle: SwitchOutputHandle = isActive ? 'active' : 'inactive'
    const outputLabel = isActive ? this.activeLabel : this.inactiveLabel

    console.log(
      `🔀 [${this.id}] Condition ${this._condition} ${this._threshold}:`,
      message.payload,
      '→',
      outputLabel,
      `(${outputHandle})`
    )

    // Forward the original payload to the selected output
    await this.send(
      {
        payload: message.payload,
        _msgid: uuidv4(),
        timestamp: Date.now(),
        metadata: {
          source: this.id,
          condition: this._condition,
          selected: outputHandle,
        },
      },
      outputHandle
    )
  }

  toSerializable(): Record<string, unknown> {
    return {
      id: this.id,
      type: this.type,
      category: this.category,
      label: this.label,
      metadata: {
        condition: this._condition,
        threshold: this._threshold,
        activeLabel: this.activeLabel,
        inactiveLabel: this.inactiveLabel,
      },
    }
  }
}
