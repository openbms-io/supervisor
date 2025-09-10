import {
  DataNode,
  LogicNode,
  LogicOutputHandle,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'

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
}
