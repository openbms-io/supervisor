import { BacnetNodeUI } from './bacnet-node-ui'
import { CalculationNode } from './calculation-node'
import { ComparisonNode } from './comparison-node'
import { WriteSetpointNode } from './write-setpoint-node'
import { ConstantNodeUI } from './constant-node-ui'
import { SwitchNode } from './switch-node'

// Strongly typed node types for React Flow
export const nodeTypes = {
  // BACnet nodes - all using unified UI
  'bacnet.analog-input': BacnetNodeUI,
  'bacnet.binary-input': BacnetNodeUI,
  'bacnet.multistate-input': BacnetNodeUI,

  'bacnet.analog-output': BacnetNodeUI,
  'bacnet.binary-output': BacnetNodeUI,
  'bacnet.multistate-output': BacnetNodeUI,

  'bacnet.analog-value': BacnetNodeUI,
  'bacnet.binary-value': BacnetNodeUI,
  'bacnet.multistate-value': BacnetNodeUI,

  // Logic nodes
  'logic.calculation': CalculationNode,
  'logic.comparison': ComparisonNode,
  'logic.constant': ConstantNodeUI,

  // Command nodes
  'command.write-setpoint': WriteSetpointNode,

  // Control flow nodes
  'control-flow.switch': SwitchNode,
} as const
