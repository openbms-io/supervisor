import {
  BacnetInputOutput,
  LogicNode,
  CommandNode,
  ControlFlowNode,
  NodeCategory,
} from './infrastructure'
import { ConstantNodeMetadata } from '@/lib/data-nodes/constant-node'
import { TimerNodeMetadata } from '@/lib/data-nodes/timer-node'

// Base node data that ensures compatibility with React Flow
// This just ensures Record<string, unknown> compatibility
export type BaseNodeData = Record<string, unknown>

// BACnet node data with specific object type
export interface BacnetNodeData extends BacnetInputOutput, BaseNodeData {
  category: NodeCategory.BACNET
}

// Logic node data types
export interface CalculationNodeData extends LogicNode, BaseNodeData {
  category: NodeCategory.LOGIC
  type: 'calculation'
  metadata?: {
    operation?: string
  }
}

export interface ComparisonNodeData extends LogicNode, BaseNodeData {
  category: NodeCategory.LOGIC
  type: 'comparison'
  metadata?: {
    operation?: string
  }
}

export interface ConstantNodeData extends LogicNode, BaseNodeData {
  category: NodeCategory.LOGIC
  type: 'constant'
  metadata: ConstantNodeMetadata
}

// Command node data types
export interface WriteSetpointNodeData extends CommandNode, BaseNodeData {
  category: NodeCategory.COMMAND
  type: 'write-setpoint'
}

// Control flow node data types
export interface SwitchNodeData extends ControlFlowNode, BaseNodeData {
  category: NodeCategory.CONTROL_FLOW
  type: 'switch'
  condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
  threshold: number
  activeLabel: string
  inactiveLabel: string
}

export interface TimerNodeData extends ControlFlowNode, BaseNodeData {
  category: NodeCategory.CONTROL_FLOW
  type: 'timer'
  metadata: TimerNodeMetadata
  // Updating ui state, without triggering a react flow update. Used for timer node.
  stateDidChange?: (stateData: { running: boolean; tickCount: number }) => void
}

// Discriminated union of all node data types
export type NodeData =
  | BacnetNodeData
  | CalculationNodeData
  | ComparisonNodeData
  | ConstantNodeData
  | WriteSetpointNodeData
  | SwitchNodeData
  | TimerNodeData

// Map node type strings to their data types
export interface NodeTypesMap {
  // BACnet nodes
  'bacnet.analog-input': BacnetNodeData
  'bacnet.analog-output': BacnetNodeData
  'bacnet.analog-value': BacnetNodeData
  'bacnet.binary-input': BacnetNodeData
  'bacnet.binary-output': BacnetNodeData
  'bacnet.binary-value': BacnetNodeData
  'bacnet.multistate-input': BacnetNodeData
  'bacnet.multistate-output': BacnetNodeData
  'bacnet.multistate-value': BacnetNodeData

  // Logic nodes
  'logic.calculation': CalculationNodeData
  'logic.comparison': ComparisonNodeData
  'logic.constant': ConstantNodeData

  // Command nodes
  'command.write-setpoint': WriteSetpointNodeData

  // Control flow nodes
  'control-flow.switch': SwitchNodeData
  'control-flow.timer': TimerNodeData
}

// Type helper to get node data type from node type string
export type NodeDataFromType<T extends keyof NodeTypesMap> = NodeTypesMap[T]
