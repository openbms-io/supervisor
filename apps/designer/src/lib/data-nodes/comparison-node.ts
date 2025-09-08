import {
  DataNode,
  NodeCategory,
  NodeDirection,
  generateInstanceId,
} from '@/types/infrastructure'

export type ComparisonOperation =
  | 'equals'
  | 'greater'
  | 'less'
  | 'greater-equal'
  | 'less-equal'

export class ComparisonNode implements DataNode {
  readonly id: string
  readonly type = 'comparison' as const
  readonly category = NodeCategory.LOGIC
  readonly label: string
  readonly direction = NodeDirection.BIDIRECTIONAL
  readonly metadata: { operation: ComparisonOperation }

  constructor(label: string, operation: ComparisonOperation) {
    this.id = generateInstanceId()
    this.label = label
    this.metadata = { operation }
  }

  canConnectWith(target: DataNode): boolean {
    // Logic nodes can connect to other logic nodes or outputs
    return target.direction !== NodeDirection.OUTPUT
  }
}
