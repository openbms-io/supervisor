import {
  LogicNode,
  ComparisonInputHandle,
  LogicOutputHandle,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
  DataNode,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export type ComparisonOperation =
  | 'equals'
  | 'greater'
  | 'less'
  | 'greater-equal'
  | 'less-equal'

export class ComparisonNode
  implements LogicNode<ComparisonInputHandle, LogicOutputHandle>
{
  readonly id: string
  readonly type = 'comparison' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: { operation: ComparisonOperation }

  // Private internal state
  private _computedValue?: boolean
  private _inputValues: ComputeValue[] = []
  private sendCallback?: SendCallback<LogicOutputHandle>
  private messageBuffer: Map<ComparisonInputHandle, Message> = new Map()

  // Public getters for UI access
  get computedValue(): boolean | undefined {
    return this._computedValue
  }

  get inputValues(): ComputeValue[] {
    return this._inputValues
  }

  constructor(label: string, operation: ComparisonOperation) {
    this.id = generateInstanceId()
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

  execute(inputs: ComputeValue[]): boolean {
    const v1 = inputs[0]
    const v2 = inputs[1]

    if (v1 === undefined || v2 === undefined) {
      this._inputValues = inputs
      this._computedValue = false
      return false
    }

    let result: boolean
    switch (this.metadata.operation) {
      case 'equals':
        result = v1 === v2
        break
      case 'greater':
        result = v1 > v2
        break
      case 'less':
        result = v1 < v2
        break
      case 'greater-equal':
        result = v1 >= v2
        break
      case 'less-equal':
        result = v1 <= v2
        break
      default:
        result = false
    }

    this._inputValues = inputs
    this._computedValue = result
    return result
  }

  canConnectWith(target: DataNode): boolean {
    // Logic nodes can connect to other logic nodes or outputs
    return target.direction !== NodeDirection.OUTPUT
  }

  getInputHandles(): readonly ComparisonInputHandle[] {
    return ['value1', 'value2'] as const
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
    handle: ComparisonInputHandle,
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
      console.log(
        `✅ [${this.id}] All inputs received, processing comparison...`
      )

      // Collect and execute
      const inputs: ComputeValue[] = requiredHandles.map(
        (h) => this.messageBuffer.get(h)?.payload ?? 0
      )

      const result = this.execute(inputs)

      console.log(
        `🔍 [${this.id}] Compared:`,
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

      // Clear buffer for next comparison
      this.messageBuffer.clear()
    } else {
      console.log(`⏳ [${this.id}] Waiting for more inputs...`)
    }
  }
}
