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
import { CalculationNode, CalculationOperation } from './calculation-node'
import { ComparisonNode, ComparisonOperation } from './comparison-node'
import { WriteSetpointNode } from './write-setpoint-node'

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
      case 'analog-output':
        return new AnalogOutputNode(config)
      case 'binary-output':
        return new BinaryOutputNode(config)
      case 'analog-value':
        return new AnalogValueNode(config)
      case 'binary-value':
        return new BinaryValueNode(config)
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
    targetPointId,
    propertyName,
  }: {
    label: string
    targetPointId?: string
    propertyName?: string
  }): DataNode {
    return new WriteSetpointNode(label, targetPointId, propertyName)
  }
}

// Export singleton instance
const factory = new DataNodeFactory()
export default factory
