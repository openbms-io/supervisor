// Example node implementations
export { AnalogInputNode } from './analog-input-node'
export { AnalogOutputNode } from './analog-output-node'
export { CalculationNode, type CalculationOperation } from './calculation-node'
export { ComparisonNode, type ComparisonOperation } from './comparison-node'
export { WriteSetpointNode } from './write-setpoint-node'
export {
  ConstantNode,
  type ValueType,
  type ConstantNodeMetadata,
} from './constant-node'
export { TimerNode, type TimerNodeMetadata } from './timer-node'
export {
  ScheduleNode,
  type ScheduleNodeMetadata,
  type ScheduleState,
  type DayOfWeek,
} from './schedule-node'

// Factory for creating nodes
export { default as nodeFactory } from './factory'
