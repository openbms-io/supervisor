import {
  ControlFlowNode,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  DataNode,
  generateInstanceId,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export type TimerInputHandle = 'trigger'
export type TimerOutputHandle = 'output'

export interface TimerNodeMetadata {
  duration: number // interval in milliseconds
}

export class TimerNode
  implements ControlFlowNode<TimerInputHandle, TimerOutputHandle>
{
  readonly id: string
  readonly category = NodeCategory.CONTROL_FLOW
  readonly type = 'timer'
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: TimerNodeMetadata

  label: string

  private _duration: number
  private _intervalId: NodeJS.Timeout | null = null
  private _isRunning: boolean = false
  public _tickCount: number = 0
  private _inputValue?: ComputeValue

  private sendCallback?: SendCallback<TimerOutputHandle>

  public stateDidChange?: (stateData: {
    running: boolean
    tickCount: number
  }) => void

  get duration(): number {
    return this._duration
  }

  get isRunning(): boolean {
    return this._isRunning
  }

  get tickCount(): number {
    return this._tickCount
  }

  get computedValue(): ComputeValue | undefined {
    return this._inputValue !== undefined ? this._inputValue : this._tickCount
  }

  constructor(label: string, duration: number = 1000) {
    this.id = generateInstanceId()
    this.label = label
    this._duration = duration
    this.metadata = { duration }
  }

  setDuration(duration: number): void {
    this._duration = Math.max(100, duration)
    ;(this.metadata as { duration: number }).duration = this._duration

    if (this._isRunning) {
      this.stop()
      this.start()
    }
  }

  getValue(): ComputeValue | undefined {
    return this.computedValue
  }

  reset(): void {
    this.stop()
    this._tickCount = 0
    this._inputValue = undefined
    this.stateDidChange?.({ running: false, tickCount: 0 })
  }

  getActiveOutputHandles(): readonly TimerOutputHandle[] {
    return this._isRunning ? (['output'] as const) : []
  }

  private start(): void {
    if (this._isRunning) return

    this._isRunning = true
    this._tickCount = 0
    this.stateDidChange?.({
      running: this._isRunning,
      tickCount: this._tickCount,
    })
    // Send first pulse immediately
    this.sendPulse()

    // Then send periodic pulses
    this._intervalId = setInterval(() => {
      this.sendPulse()
    }, this._duration)
  }

  private stop(): void {
    if (this._intervalId) {
      clearInterval(this._intervalId)
      this._intervalId = null
    }
    this._isRunning = false
    this.stateDidChange?.({ running: false, tickCount: this._tickCount })
  }

  private sendPulse(): void {
    this._tickCount++
    this.stateDidChange?.({
      running: this._isRunning,
      tickCount: this._tickCount,
    })
    this.sendOutput()
  }

  private async sendOutput(): Promise<void> {
    const payload =
      this._inputValue !== undefined ? this._inputValue : this._tickCount

    if (this.sendCallback && payload !== undefined) {
      await this.send(
        {
          payload,
          _msgid: uuidv4(),
          timestamp: Date.now(),
          metadata: {
            source: this.id,
            type: 'timer',
            tick: this._tickCount,
          },
        },
        'output'
      )
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  canConnectWith(_other: DataNode): boolean {
    return true
  }

  getInputHandles(): readonly TimerInputHandle[] {
    return ['trigger'] as const
  }

  getOutputHandles(): readonly TimerOutputHandle[] {
    return ['output'] as const
  }

  setSendCallback(callback: SendCallback<TimerOutputHandle>): void {
    this.sendCallback = callback
  }

  private async send(
    message: Message,
    handle: TimerOutputHandle
  ): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    message: Message,
    handle: TimerInputHandle,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `⏱️ [${this.id}] Timer received on ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    this._inputValue = message.payload

    // Simple: truthy starts, falsy stops
    if (message.payload) {
      this.start()
    } else {
      this.stop()
    }
  }

  // For source node behavior
  async trigger(): Promise<void> {
    if (this._inputValue === undefined) {
      this.start()
    }
  }
}
