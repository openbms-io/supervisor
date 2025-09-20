import {
  LogicNode,
  CalculationInputHandle,
  LogicOutputHandle,
  ComputeValue,
  NodeCategory,
  NodeType,
  NodeDirection,
  generateInstanceId,
  DataNode,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'
import { makeSerializable } from '@/lib/workflow/serialization-utils'

export type CalculationOperation =
  | 'add'
  | 'subtract'
  | 'multiply'
  | 'divide'
  | 'average'

export class CalculationNode
  implements LogicNode<CalculationInputHandle, LogicOutputHandle>
{
  readonly id: string
  readonly type = NodeType.CALCULATION
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: { operation: CalculationOperation }

  // Private internal state
  private _computedValue?: number
  private _inputValues: ComputeValue[] = []
  private sendCallback?: SendCallback<LogicOutputHandle>
  private messageBuffer: Map<CalculationInputHandle, Message> = new Map()

  // Public getters for UI access
  get computedValue(): number | undefined {
    return this._computedValue
  }

  get inputValues(): ComputeValue[] {
    return this._inputValues
  }

  constructor(label: string, operation: CalculationOperation, id?: string) {
    this.id = id || generateInstanceId()
    this.label = label
    this.metadata = { operation }
  }

  getValue(): ComputeValue | undefined {
    return this._computedValue
  }

  getInputValues(): ComputeValue[] {
    return this._inputValues
  }

  reset(): void {
    this._computedValue = undefined
    this._inputValues = []
    this.messageBuffer.clear()
  }

  private execute(inputs: ComputeValue[]): number {
    // Convert boolean to number: true=1, false=0
    const num1 = typeof inputs[0] === 'number' ? inputs[0] : inputs[0] ? 1 : 0
    const num2 = typeof inputs[1] === 'number' ? inputs[1] : inputs[1] ? 1 : 0

    let result: number
    switch (this.metadata.operation) {
      case 'add':
        result = num1 + num2
        break
      case 'subtract':
        result = num1 - num2
        break
      case 'multiply':
        result = num1 * num2
        break
      case 'divide':
        result = num2 !== 0 ? num1 / num2 : NaN
        break
      case 'average':
        result = (num1 + num2) / 2
        break
      default:
        result = NaN
    }

    this._inputValues = inputs
    this._computedValue = result
    return result
  }

  canConnectWith(target: DataNode): boolean {
    // Logic nodes can connect to other logic nodes or outputs
    // Cannot connect to pure input nodes
    return target.direction !== NodeDirection.OUTPUT
  }

  getInputHandles(): readonly CalculationInputHandle[] {
    return ['input1', 'input2'] as const
  }

  getOutputHandles(): readonly LogicOutputHandle[] {
    return ['output'] as const
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
    message: Message,
    handle: CalculationInputHandle,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `📥 [${this.id}] Received on ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    // Buffer the message
    this.messageBuffer.set(handle, message)

    // Check if we have all inputs
    const requiredHandles = this.getInputHandles()
    const hasAllInputs = requiredHandles.every((h) => this.messageBuffer.has(h))

    if (hasAllInputs) {
      console.log(`✅ [${this.id}] All inputs received, processing...`)

      // Collect and execute
      const inputs: ComputeValue[] = requiredHandles.map(
        (h) => this.messageBuffer.get(h)?.payload ?? 0
      )

      const result = this.execute(inputs)

      console.log(
        `🧮 [${this.id}] Computed:`,
        inputs[0],
        this.metadata.operation,
        inputs[1],
        '=',
        result
      )

      // Send result - this triggers downstream nodes!
      await this.send(
        {
          payload: result,
          _msgid: uuidv4(),
          timestamp: Date.now(),
          metadata: { source: this.id, operation: this.metadata.operation },
        },
        'output'
      )

      // Clear buffer for next calculation
      this.messageBuffer.clear()
    } else {
      console.log(`⏳ [${this.id}] Waiting for more inputs...`)
    }
  }

  toSerializable(): Record<string, unknown> {
    const metadata: { operation: CalculationOperation } = this.metadata
    return makeSerializable<
      { operation: CalculationOperation },
      NodeType.CALCULATION,
      NodeCategory.LOGIC
    >({
      id: this.id,
      type: this.type,
      category: this.category,
      label: this.label,
      metadata,
    })
  }
}
