import { BacnetInputNode } from './bacnet-input-node'
import { BacnetOutputNode } from './bacnet-output-node'
import { BacnetValueNode } from './bacnet-value-node'
import { CalculationNode } from './calculation-node'
import { ComparisonNode } from './comparison-node'
import { WriteSetpointNode } from './write-setpoint-node'

// Strongly typed node types for React Flow
export const nodeTypes = {
  // BACnet nodes
  'bacnet.analog-input': BacnetInputNode,
  'bacnet.binary-input': BacnetInputNode,
  'bacnet.multistate-input': BacnetInputNode,

  'bacnet.analog-output': BacnetOutputNode,
  'bacnet.binary-output': BacnetOutputNode,
  'bacnet.multistate-output': BacnetOutputNode,

  'bacnet.analog-value': BacnetValueNode,
  'bacnet.binary-value': BacnetValueNode,
  'bacnet.multistate-value': BacnetValueNode,

  // Logic nodes
  'logic.calculation': CalculationNode,
  'logic.comparison': ComparisonNode,

  // Command nodes
  'command.write-setpoint': WriteSetpointNode,
}
