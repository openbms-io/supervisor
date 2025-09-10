import {
  LogicNode,
  CalculationInputHandle,
  LogicOutputHandle,
  ComputeValue,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
  DataNode,
} from '@/types/infrastructure'

export type CalculationOperation =
  | 'add'
  | 'subtract'
  | 'multiply'
  | 'divide'
  | 'average'

export class CalculationNode
  implements LogicNode<CalculationInputHandle, LogicOutputHandle>
{
  readonly id: string
  readonly type = 'calculation' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: { operation: CalculationOperation }

  // Private internal state
  private _computedValue?: number
  private _inputValues: ComputeValue[] = []

  // Public getters for UI access
  get computedValue(): number | undefined {
    return this._computedValue
  }

  get inputValues(): ComputeValue[] {
    return this._inputValues
  }

  constructor(label: string, operation: CalculationOperation) {
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

  execute(inputs: ComputeValue[]): number {
    // Convert boolean to number: true=1, false=0
    const num1 = typeof inputs[0] === 'number' ? inputs[0] : inputs[0] ? 1 : 0
    const num2 = typeof inputs[1] === 'number' ? inputs[1] : inputs[1] ? 1 : 0

    let result: number
    switch (this.metadata.operation) {
      case 'add':
        result = num1 + num2
        break
      case 'subtract':
        result = num1 - num2
        break
      case 'multiply':
        result = num1 * num2
        break
      case 'divide':
        result = num2 !== 0 ? num1 / num2 : NaN
        break
      case 'average':
        result = (num1 + num2) / 2
        break
      default:
        result = NaN
    }

    this._inputValues = inputs
    this._computedValue = result
    return result
  }

  canConnectWith(target: DataNode): boolean {
    // Logic nodes can connect to other logic nodes or outputs
    // Cannot connect to pure input nodes
    return target.direction !== NodeDirection.OUTPUT
  }

  getInputHandles(): readonly CalculationInputHandle[] {
    return ['input1', 'input2'] as const
  }

  getOutputHandles(): readonly LogicOutputHandle[] {
    return ['output'] as const
  }
}
