import {
  LogicNode,
  LogicOutputHandle,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
  DataNode,
} from '@/types/infrastructure'

export type MemoryInputHandle = 'value' | 'write' | 'reset'
export type MemoryValueType = 'number' | 'boolean'

export interface MemoryNodeMetadata {
  initValue: number | boolean
  valueType: MemoryValueType
}

export class MemoryNode
  implements LogicNode<MemoryInputHandle, LogicOutputHandle>
{
  readonly id: string
  readonly type = 'memory' as const
  readonly category = NodeCategory.LOGIC
  readonly direction = NodeDirection.BIDIRECTIONAL

  label: string

  private _metadata: MemoryNodeMetadata

  // Stored state (committed between runs within session)
  private _storedValue?: ComputeValue

  // Output sampled at start of execute
  private _computedValue?: ComputeValue

  constructor(
    label: string,
    initValue: number | boolean = 0,
    valueType: MemoryValueType = 'number'
  ) {
    this.id = generateInstanceId()
    this.label = label
    this._metadata = { initValue, valueType }
  }

  // Public metadata accessor
  get metadata(): MemoryNodeMetadata {
    return this._metadata
  }

  // Read-only current output for UI
  get computedValue(): ComputeValue | undefined {
    return this._computedValue
  }

  getValue(): ComputeValue | undefined {
    return this._computedValue
  }

  reset(): void {
    // For Designer preview, reset output and clear stored session state
    this._computedValue = undefined
    this._storedValue = undefined
  }

  canConnectWith(target: DataNode): boolean {
    return target.direction !== NodeDirection.OUTPUT
  }

  getInputHandles(): readonly MemoryInputHandle[] {
    return ['value', 'write', 'reset'] as const
  }

  getOutputHandles(): readonly LogicOutputHandle[] {
    return ['output'] as const
  }

  // Execute with sample-then-commit semantics within a single run
  execute(inputs: ComputeValue[]): ComputeValue {
    const [inValue, write, reset] = inputs

    // 1) Sample current state for this tick's output
    const current =
      this._storedValue !== undefined
        ? this._storedValue
        : this._metadata.initValue
    this._computedValue = current

    // 2) Apply Reset or Write to update stored state for next tick/run
    const writeTruthy = typeof write === 'number' ? write !== 0 : !!write
    const resetTruthy = typeof reset === 'number' ? reset !== 0 : !!reset

    if (resetTruthy) {
      this._storedValue = this._metadata.initValue
    } else if (writeTruthy) {
      this._storedValue =
        this._metadata.valueType === 'boolean'
          ? Boolean(inValue)
          : Number(inValue)
    }

    return this._computedValue
  }

  // Encapsulated updates from UI
  setInitValue(value: number | boolean): void {
    this._metadata = { ...this._metadata, initValue: value }
    // If we had no stored value yet, the visible output next run will reflect new init
  }

  setValueType(valueType: MemoryValueType): void {
    let newInit: number | boolean
    switch (valueType) {
      case 'number':
        newInit = 0
        break
      case 'boolean':
        newInit = false
        break
    }
    this._metadata = { valueType, initValue: newInit }
    // Clear stored so the next run starts from the new init
    this._storedValue = undefined
  }
}
