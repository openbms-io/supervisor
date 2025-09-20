import {
  ControlFlowNode,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  DataNode,
  generateInstanceId,
  ScheduleInputHandle,
  ScheduleOutputHandle,
} from '@/types/infrastructure'
import { Message, SendCallback } from '@/lib/message-system/types'
import { v4 as uuidv4 } from 'uuid'

export type DayOfWeek = 'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun'

export interface ScheduleNodeMetadata {
  startTime: string
  endTime: string
  days: DayOfWeek[]
}

// Single state interface for both internal and UI
export interface ScheduleState {
  startTime: string
  endTime: string
  days: DayOfWeek[]
  isActive: boolean
  isEnabled: boolean
}

export class ScheduleNode
  implements ControlFlowNode<ScheduleInputHandle, ScheduleOutputHandle>
{
  readonly id: string
  readonly category = NodeCategory.CONTROL_FLOW
  readonly type = 'schedule'
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: ScheduleNodeMetadata

  label: string

  // Single state object
  private state: ScheduleState
  private _checkIntervalId: NodeJS.Timeout | null = null
  private _inputValue?: ComputeValue
  private sendCallback?: SendCallback<ScheduleOutputHandle>

  // Callback to update UI
  public stateDidChange?: (state: ScheduleState) => void

  get isActive(): boolean {
    return this.state.isActive
  }

  get computedValue(): ComputeValue | undefined {
    return this.state.isActive
  }

  constructor(
    label: string,
    startTime: string = '08:00',
    endTime: string = '17:00',
    days: DayOfWeek[] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    id?: string
  ) {
    this.id = id || generateInstanceId()
    this.label = label

    // Initialize single state
    this.state = {
      startTime,
      endTime,
      days,
      isActive: false,
      isEnabled: false,
    }

    this.metadata = { startTime, endTime, days }
  }

  setSchedule(startTime: string, endTime: string, days: DayOfWeek[]): void {
    // Update state
    this.state.startTime = startTime
    this.state.endTime = endTime
    this.state.days = days

    // Update metadata
    ;(this.metadata as ScheduleNodeMetadata) = { startTime, endTime, days }

    if (this.state.isEnabled) {
      this.checkSchedule()
    }

    // Notify UI
    this.notifyStateChange()
  }

  getValue(): ComputeValue | undefined {
    return this.computedValue
  }

  reset(): void {
    this.stop()
    this._inputValue = undefined
  }

  getActiveOutputHandles(): readonly ScheduleOutputHandle[] {
    return this.state.isActive ? ['output' as const] : []
  }

  private start(): void {
    if (this.state.isEnabled) return

    this.state.isEnabled = true
    this.checkSchedule()

    this._checkIntervalId = setInterval(() => {
      this.checkSchedule()
    }, 60000)

    this.notifyStateChange()
  }

  private stop(): void {
    if (this._checkIntervalId) {
      clearInterval(this._checkIntervalId)
      this._checkIntervalId = null
    }

    this.state.isEnabled = false
    this.state.isActive = false

    this.notifyStateChange()
  }

  private getCurrentDay(): DayOfWeek {
    const days: DayOfWeek[] = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return days[new Date().getDay()]
  }

  private checkSchedule(): void {
    const now = new Date()
    const currentDay = this.getCurrentDay()
    const currentMinutes = now.getHours() * 60 + now.getMinutes()

    const wasActive = this.state.isActive

    // Check if today is selected
    if (!this.state.days.includes(currentDay)) {
      this.state.isActive = false
    } else {
      // Check time
      const [startHour, startMin] = this.state.startTime.split(':').map(Number)
      const [endHour, endMin] = this.state.endTime.split(':').map(Number)

      const startMinutes = startHour * 60 + startMin
      const endMinutes = endHour * 60 + endMin

      if (endMinutes < startMinutes) {
        this.state.isActive =
          currentMinutes >= startMinutes || currentMinutes < endMinutes
      } else {
        this.state.isActive =
          currentMinutes >= startMinutes && currentMinutes < endMinutes
      }
    }

    this.notifyStateChange()

    if (wasActive !== this.state.isActive) {
      this.sendOutput()
    }
  }

  private notifyStateChange(): void {
    // Send entire state object to UI
    this.stateDidChange?.({ ...this.state })
  }

  private async sendOutput(): Promise<void> {
    // Send trigger when schedule state changes
    const payload =
      this._inputValue !== undefined ? this._inputValue : this.state.isActive

    if (this.sendCallback && payload !== undefined) {
      await this.send(
        {
          payload,
          _msgid: uuidv4(),
          timestamp: Date.now(),
          metadata: {
            source: this.id,
            type: 'schedule',
            active: this.state.isActive,
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

  getInputHandles(): readonly ScheduleInputHandle[] {
    return ['input'] as const
  }

  getOutputHandles(): readonly ScheduleOutputHandle[] {
    return ['output'] as const
  }

  setSendCallback(callback: SendCallback<ScheduleOutputHandle>): void {
    this.sendCallback = callback
  }

  private async send(
    message: Message,
    handle: ScheduleOutputHandle
  ): Promise<void> {
    if (this.sendCallback) {
      await this.sendCallback(message, this.id, handle)
    }
  }

  async receive(
    message: Message,
    handle: ScheduleInputHandle,
    fromNodeId: string
  ): Promise<void> {
    console.log(
      `📅 [${this.id}] Schedule received on ${handle}:`,
      message.payload,
      `from ${fromNodeId}`
    )

    this._inputValue = message.payload

    if (message.payload) {
      this.start()
    } else {
      this.stop()
    }
  }

  toSerializable(): Record<string, unknown> {
    return {
      id: this.id,
      type: this.type,
      category: this.category,
      label: this.label,
      metadata: this.metadata,
    }
  }
}
