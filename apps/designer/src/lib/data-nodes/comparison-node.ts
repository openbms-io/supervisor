import {
  LogicNode,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
  DataNode,
} from '@/types/infrastructure'

export type ComparisonOperation =
  | 'equals'
  | 'greater'
  | 'less'
  | 'greater-equal'
  | 'less-equal'

export class ComparisonNode implements LogicNode {
  readonly id: string
  readonly type = 'comparison' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: { operation: ComparisonOperation }

  inputValues: ComputeValue[] = []
  computedValue?: boolean
  lastComputed?: Date

  constructor(label: string, operation: ComparisonOperation) {
    this.id = generateInstanceId()
    this.label = label
    this.metadata = { operation }
  }

  execute(inputs: ComputeValue[]): boolean {
    const v1 = inputs[0]
    const v2 = inputs[1]

    if (v1 === undefined || v2 === undefined) {
      this.computedValue = false
      this.inputValues = inputs
      this.lastComputed = new Date()
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

    this.inputValues = inputs
    this.computedValue = result
    this.lastComputed = new Date()
    return result
  }

  canConnectWith(target: DataNode): boolean {
    // Logic nodes can connect to other logic nodes or outputs
    return target.direction !== NodeDirection.OUTPUT
  }
}
