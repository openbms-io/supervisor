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
  readonly direction = NodeDirection.OUTPUT // Constants only output values
  readonly metadata: ConstantNodeMetadata

  // LogicNode interface fields
  inputValues: ComputeValue[] = [] // Constants have no inputs
  computedValue?: ComputeValue
  lastComputed?: Date

  constructor(
    label: string,
    value: number | boolean | string = 0,
    valueType: ValueType = 'number'
  ) {
    this.id = generateInstanceId()
    this.label = label
    this.metadata = { value, valueType }

    // Initialize computedValue if the value is a valid ComputeValue
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
    // Create new metadata object to avoid mutation
    ;(this as any).metadata = { ...this.metadata, value }

    // Update computedValue if it's a valid ComputeValue
    if (typeof value === 'number' || typeof value === 'boolean') {
      this.computedValue = value
      this.lastComputed = new Date()
    } else {
      this.computedValue = undefined
    }
  }

  setValueType(valueType: ValueType): void {
    // Reset value to appropriate default
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
    // Create new metadata object to avoid mutation
    ;(this as any).metadata = { valueType, value: newValue }

    // Update computedValue if it's a valid ComputeValue
    if (typeof newValue === 'number' || typeof newValue === 'boolean') {
      this.computedValue = newValue
      this.lastComputed = new Date()
    } else {
      this.computedValue = undefined
    }
  }
}
