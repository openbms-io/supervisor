import { DataNode, BacnetConfig } from '@/types/infrastructure'
import { AnalogInputNode } from './analog-input-node'
import { AnalogOutputNode } from './analog-output-node'
import { CalculationNode, CalculationOperation } from './calculation-node'
import { WriteSetpointNode } from './write-setpoint-node'

// Simple factory pattern for creating nodes
class DataNodeFactory {
  // Create appropriate node from BACnet config
  createDataNodeFromBacnetConfig({
    config,
  }: {
    config: BacnetConfig
  }): DataNode {
    const { objectType } = config

    // Create appropriate node based on object type
    switch (objectType) {
      case 'analog-input':
      case 'binary-input':
        return new AnalogInputNode(config)

      case 'analog-output':
      case 'binary-output':
        return new AnalogOutputNode(config)

      default:
        // Values can be inputs (sensors) or outputs (setpoints)
        // This would be determined by context in real app
        return new AnalogInputNode(config)
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

  // Create command node
  createWriteSetpointNode({
    label,
    targetPointId,
  }: {
    label: string
    targetPointId?: string
  }): DataNode {
    return new WriteSetpointNode(label, targetPointId, 'presentValue')
  }
}

// Export singleton instance
const factory = new DataNodeFactory()
export default factory
