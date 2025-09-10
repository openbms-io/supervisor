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
  private _computedValue?: ComputeValue
  private _condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
  private _threshold: number

  // Public getters for UI access
  get computedValue(): ComputeValue | undefined {
    return this._computedValue
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
    inactiveLabel?: string
  ) {
    this.id = generateInstanceId()
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
    return this._computedValue
  }

  reset(): void {
    this._computedValue = undefined
  }

  private evaluate(): boolean {
    if (this._computedValue === undefined) return false

    const value = Number(this._computedValue)
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

  execute(inputs: ComputeValue[]): void {
    this._computedValue = inputs[0]
  }

  getActiveOutputHandles(): readonly SwitchOutputHandle[] {
    const isActive = this.evaluate()
    const handle: SwitchOutputHandle = isActive ? 'active' : 'inactive'
    return [handle] as const
  }
}
