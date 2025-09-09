import {
  DataNode,
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

export class ConstantNode implements DataNode {
  readonly id: string
  readonly type = 'constant' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.OUTPUT // Constants only output values
  readonly metadata: ConstantNodeMetadata

  constructor(
    label: string,
    value: number | boolean | string = 0,
    valueType: ValueType = 'number'
  ) {
    this.id = generateInstanceId()
    this.label = label
    this.metadata = { value, valueType }
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
    this.metadata.value = value
  }

  setValueType(valueType: ValueType): void {
    this.metadata.valueType = valueType
    // Reset value to appropriate default
    switch (valueType) {
      case 'number':
        this.metadata.value = 0
        break
      case 'boolean':
        this.metadata.value = false
        break
      case 'string':
        this.metadata.value = ''
        break
    }
  }
}
