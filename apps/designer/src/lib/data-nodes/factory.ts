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
import { TimerNode } from './timer-node'
import { ScheduleNode, DayOfWeek } from './schedule-node'
import { FunctionNode, FunctionInput } from './function-node'

// Simple factory pattern for creating nodes
class DataNodeFactory {
  // Create appropriate node from BACnet config
  createDataNodeFromBacnetConfig({
    config,
    id,
  }: {
    config: BacnetConfig
    id?: string
  }): BacnetInputOutput {
    const { objectType } = config

    // Create appropriate node based on object type
    switch (objectType) {
      case 'analog-input':
        return new AnalogInputNode(config, id)
      case 'binary-input':
        return new BinaryInputNode(config, id)
      case 'multistate-input':
        return new MultistateInputNode(config, id)
      case 'analog-output':
        return new AnalogOutputNode(config, id)
      case 'binary-output':
        return new BinaryOutputNode(config, id)
      case 'multistate-output':
        return new MultistateOutputNode(config, id)
      case 'analog-value':
        return new AnalogValueNode(config, id)
      case 'binary-value':
        return new BinaryValueNode(config, id)
      case 'multistate-value':
        return new MultistateValueNode(config, id)
      default:
        throw new Error(`Unsupported BACnet object type: ${objectType}`)
    }
  }

  // Create logic node
  createCalculationNode({
    label,
    operation,
    id,
  }: {
    label: string
    operation: CalculationOperation
    id?: string
  }): DataNode {
    return new CalculationNode(label, operation, id)
  }

  // Create comparison node
  createComparisonNode({
    label,
    operation,
    id,
  }: {
    label: string
    operation: ComparisonOperation
    id?: string
  }): DataNode {
    return new ComparisonNode(label, operation, id)
  }

  createWriteSetpointNode({
    label,
    priority = 8,
    id,
  }: {
    label: string
    priority?: number
    id?: string
  }): DataNode {
    return new WriteSetpointNode(label, priority, id)
  }

  createConstantNode({
    label,
    value,
    valueType,
    id,
  }: {
    label: string
    value?: number | boolean | string
    valueType?: ValueType
    id?: string
  }): DataNode {
    return new ConstantNode(label, value ?? 0, valueType ?? 'number', id)
  }

  createSwitchNode({
    label,
    condition,
    threshold,
    activeLabel,
    inactiveLabel,
    id,
  }: {
    label?: string
    condition?: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
    threshold?: number
    activeLabel?: string
    inactiveLabel?: string
    id?: string
  }): SwitchNode {
    return new SwitchNode(
      label || 'Switch',
      condition || 'gt',
      threshold || 0,
      activeLabel,
      inactiveLabel,
      id
    )
  }

  createTimerNode({
    label,
    duration,
    id,
  }: {
    label?: string
    duration?: number
    id?: string
  }): TimerNode {
    return new TimerNode(label || 'Timer', duration || 1000, id)
  }

  createScheduleNode({
    label,
    startTime,
    endTime,
    days,
    id,
  }: {
    label?: string
    startTime?: string
    endTime?: string
    days?: DayOfWeek[]
    id?: string
  }): ScheduleNode {
    return new ScheduleNode(
      label || 'Schedule',
      startTime || '08:00',
      endTime || '17:00',
      days || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      id
    )
  }

  createFunctionNode({
    label,
    code,
    inputs,
    timeout,
    id,
  }: {
    label?: string
    code?: string
    inputs?: FunctionInput[]
    timeout?: number
    id?: string
  }): FunctionNode {
    return new FunctionNode(
      label || 'Function',
      {
        code,
        inputs,
        timeout,
      },
      id
    )
  }
}

const factory = new DataNodeFactory()
export default factory
