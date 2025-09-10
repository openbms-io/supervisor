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
}
