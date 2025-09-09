import {
  DataNode,
  LogicNode,
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

export class ConstantNode implements LogicNode {
  readonly id: string
  readonly type = 'constant' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.OUTPUT

  private _metadata: ConstantNodeMetadata

  get metadata(): ConstantNodeMetadata {
    return this._metadata
  }

  inputValues: ComputeValue[] = []
  computedValue?: ComputeValue
  lastComputed?: Date

  constructor(
    label: string,
    value: number | boolean | string = 0,
    valueType: ValueType = 'number'
  ) {
    this.id = generateInstanceId()
    this.label = label
    this._metadata = { value, valueType }

    if (typeof value === 'number' || typeof value === 'boolean') {
      this.computedValue = value
      this.lastComputed = new Date()
    }
  }

  canConnectWith(target: DataNode): boolean {
    // Constants can connect to anything that accepts input
    // (anything except pure output nodes)
    return target.direction !== NodeDirection.OUTPUT
  }

  getValue(): number | boolean | string {
    return this.metadata.value
  }

  setValue(value: number | boolean | string): void {
    this._metadata = { ...this._metadata, value }

    if (typeof value === 'number' || typeof value === 'boolean') {
      this.computedValue = value
      this.lastComputed = new Date()
    } else {
      this.computedValue = undefined
    }
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

    if (typeof newValue === 'number' || typeof newValue === 'boolean') {
      this.computedValue = newValue
      this.lastComputed = new Date()
    } else {
      this.computedValue = undefined
    }
  }
}
