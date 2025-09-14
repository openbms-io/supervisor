import {
  DataNode,
  BacnetConfig,
  BacnetInputOutput,
} from '@/types/infrastructure'
import { AnalogInputNode } from './analog-input-node'
import { AnalogOutputNode } from './analog-output-node'
import { AnalogValueNode } from './analog-value-node'
import { BinaryInputNode } from './binary-input-node'
import { BinaryOutputNode } from './binary-output-node'
import { BinaryValueNode } from './binary-value-node'
import { MultistateInputNode } from './multistate-input-node'
import { MultistateOutputNode } from './multistate-output-node'
import { MultistateValueNode } from './multistate-value-node'
import { CalculationNode, CalculationOperation } from './calculation-node'
import { ComparisonNode, ComparisonOperation } from './comparison-node'
import { WriteSetpointNode } from './write-setpoint-node'
import { ConstantNode, ValueType } from './constant-node'
import { SwitchNode } from './switch-node'
import { TimerNode, TimerMode } from './timer-node'

// Simple factory pattern for creating nodes
class DataNodeFactory {
  // Create appropriate node from BACnet config
  createDataNodeFromBacnetConfig({
    config,
  }: {
    config: BacnetConfig
  }): BacnetInputOutput {
    const { objectType } = config

    // Create appropriate node based on object type
    switch (objectType) {
      case 'analog-input':
        return new AnalogInputNode(config)
      case 'binary-input':
        return new BinaryInputNode(config)
      case 'multistate-input':
        return new MultistateInputNode(config)
      case 'analog-output':
        return new AnalogOutputNode(config)
      case 'binary-output':
        return new BinaryOutputNode(config)
      case 'multistate-output':
        return new MultistateOutputNode(config)
      case 'analog-value':
        return new AnalogValueNode(config)
      case 'binary-value':
        return new BinaryValueNode(config)
      case 'multistate-value':
        return new MultistateValueNode(config)
      default:
        throw new Error(`Unsupported BACnet object type: ${objectType}`)
    }
  }

  // Create logic node
  createCalculationNode({
    label,
    operation,
  }: {
    label: string
    operation: CalculationOperation
  }): DataNode {
    return new CalculationNode(label, operation)
  }

  // Create comparison node
  createComparisonNode({
    label,
    operation,
  }: {
    label: string
    operation: ComparisonOperation
  }): DataNode {
    return new ComparisonNode(label, operation)
  }

  // Create command node
  createWriteSetpointNode({
    label,
    priority = 8,
  }: {
    label: string
    priority?: number
  }): DataNode {
    return new WriteSetpointNode(label, priority)
  }

  // Create constant node
  createConstantNode({
    label,
    value,
    valueType,
  }: {
    label: string
    value?: number | boolean | string
    valueType?: ValueType
  }): DataNode {
    return new ConstantNode(label, value ?? 0, valueType ?? 'number')
  }

  // Create switch node
  createSwitchNode({
    label,
    condition,
    threshold,
    activeLabel,
    inactiveLabel,
  }: {
    label?: string
    condition?: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
    threshold?: number
    activeLabel?: string
    inactiveLabel?: string
  }): SwitchNode {
    return new SwitchNode(
      label || 'Switch',
      condition || 'gt',
      threshold || 0,
      activeLabel,
      inactiveLabel
    )
  }

  // Create timer node
  createTimerNode({
    label,
    duration,
    mode,
  }: {
    label?: string
    duration?: number
    mode?: TimerMode
  }): TimerNode {
    return new TimerNode(label || 'Timer', duration || 1000, mode || 'delay')
  }
}

// Export singleton instance
const factory = new DataNodeFactory()
export default factory
