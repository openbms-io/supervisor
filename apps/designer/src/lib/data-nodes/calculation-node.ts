import {
  DataNode,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'

export type CalculationOperation =
  | 'add'
  | 'subtract'
  | 'multiply'
  | 'divide'
  | 'average'

// Example logic node for calculations
export class CalculationNode implements DataNode {
  readonly id: string
  readonly type = 'calculation' as const
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: { operation: CalculationOperation }

  constructor(label: string, operation: CalculationOperation) {
    this.id = generateInstanceId()
    this.label = label
    this.metadata = { operation }
  }

  canConnectWith(target: DataNode): boolean {
    // Logic nodes can connect to other logic nodes or outputs
    // Cannot connect to pure input nodes
    return target.direction !== NodeDirection.OUTPUT
  }
}
