import {
  BacnetInputOutput,
  LogicNode,
  CommandNode,
  ControlFlowNode,
  NodeCategory,
  ComputeValue,
} from './infrastructure'
import { ConstantNodeMetadata } from '@/lib/data-nodes/constant-node'
import { TimerNodeMetadata } from '@/lib/data-nodes/timer-node'
import {
  ScheduleNodeMetadata,
  ScheduleState,
} from '@/lib/data-nodes/schedule-node'
import { FunctionNodeMetadata } from '@/lib/data-nodes/function-node'

/**
  - React Flow UI node data types
  -
  - These interfaces type the view-layer node.data for React Flow by composing
  - the domain contracts from '@/types/infrastructure' (DataNode/LogicNode/CommandNode)
  - and, when needed, extending with UI-only fields (e.g., lastError, stateDidChange).
  -
  - Not duplication:
  -
      - The single source of truth for behavior/shape is in '@/types/infrastructure'
  - and the classes under 'lib/data-nodes' that implement those interfaces.
  -
      - UI types here exist to make components type-safe and to allow UI-only fields
  - without polluting domain classes.
  -
  - Why separate:
  -
      - Separation of concerns: domain behavior vs. UI/view concerns.
  -
      - Structural typing: we store domain class instances directly in React Flow
  - node.data; they satisfy these interfaces at runtime.
  -
      - Flexibility: add/remove UI-only fields here without changing domain code.
  -
  - Maintenance:
  -
      - Change domain fields in '@/types/infrastructure' and the matching class in
  - 'lib/data-nodes'; these UI types inherit automatically.
  -
      - Only update this file when introducing/removing UI-only fields.
  -
  - Example:
  -
      - WriteSetpointNode implements CommandNode (domain)
  -
      - WriteSetpointNodeData extends CommandNode (UI), adding view-specific fields
  */

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

export interface FunctionNodeData extends LogicNode, BaseNodeData {
  category: NodeCategory.LOGIC
  type: 'function'
  metadata: FunctionNodeMetadata
  lastError?: string
  consoleLogs?: string[]
  stateDidChange?: (stateData: {
    result?: ComputeValue
    error?: string
    consoleLogs: string[]
  }) => void
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

export interface ScheduleNodeData extends ControlFlowNode, BaseNodeData {
  category: NodeCategory.CONTROL_FLOW
  type: 'schedule'
  metadata: ScheduleNodeMetadata
  // Single state object callback
  stateDidChange?: (state: ScheduleState) => void
}

// Discriminated union of all node data types
export type NodeData =
  | BacnetNodeData
  | CalculationNodeData
  | ComparisonNodeData
  | ConstantNodeData
  | FunctionNodeData
  | WriteSetpointNodeData
  | SwitchNodeData
  | TimerNodeData
  | ScheduleNodeData

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
  'logic.function': FunctionNodeData

  // Command nodes
  'command.write-setpoint': WriteSetpointNodeData

  // Control flow nodes
  'control-flow.switch': SwitchNodeData
  'control-flow.timer': TimerNodeData
  'control-flow.schedule': ScheduleNodeData
}

// Type helper to get node data type from node type string
export type NodeDataFromType<T extends keyof NodeTypesMap> = NodeTypesMap[T]
