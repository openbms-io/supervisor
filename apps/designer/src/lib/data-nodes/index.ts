// Example node implementations
export { AnalogInputNode } from './analog-input-node'
export { AnalogOutputNode } from './analog-output-node'
export { CalculationNode, type CalculationOperation } from './calculation-node'
export { WriteSetpointNode } from './write-setpoint-node'

// Factory for creating nodes
export { default as nodeFactory } from './factory'
