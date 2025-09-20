import { z } from 'zod'
import { Node, Edge } from '@xyflow/react'
import { getVersionMetadata, type Version } from 'bms-schemas'
import {
  WorkflowConfigSchema as StrictWorkflowConfigSchema,
  VersionedWorkflowConfigSchema as StrictVersionedWorkflowConfigSchema,
} from '@/lib/workflow/config-schema'
import {
  serializeNodeData,
  deserializeNodeData,
  type SerializedNodeData,
} from '../node-serializer'
import factory from '@/lib/data-nodes/factory'
import { type ConstantNodeMetadata } from '@/lib/data-nodes/constant-node'
import { type CalculationOperation } from '@/lib/data-nodes/calculation-node'
import { type ComparisonOperation } from '@/lib/data-nodes/comparison-node'
import { type DayOfWeek } from '@/lib/data-nodes/schedule-node'
import { type FunctionNodeMetadata } from '@/lib/data-nodes/function-node'
import { type TimerNodeMetadata } from '@/lib/data-nodes/timer-node'
import { type ScheduleNodeMetadata } from '@/lib/data-nodes/schedule-node'
import { type BacnetConfig } from '@/types/infrastructure'
import { type SwitchNodeMetadata } from '@/lib/data-nodes/switch-node'

export interface WorkflowMetadata {
  readonly lastModified: string
  readonly createdBy?: string
  readonly description?: string
}

export interface SerializedNode {
  readonly id: string
  readonly type: string
  readonly position: { readonly x: number; readonly y: number }
  readonly data: SerializedNodeData
}

export interface WorkflowConfig {
  readonly metadata: WorkflowMetadata
  readonly nodes: SerializedNode[]
  readonly edges: Edge[]
}

export interface ReactFlowObject {
  readonly nodes: Node<Record<string, unknown>>[]
  readonly edges: Edge[]
  readonly viewport: {
    readonly x: number
    readonly y: number
    readonly zoom: number
  }
}

export interface DeserializedWorkflowState {
  readonly nodes: Node<Record<string, unknown>>[]
  readonly edges: Edge[]
  readonly metadata: WorkflowMetadata
}

export interface ValidationResult {
  readonly isValid: boolean
  readonly errors: string[]
}

export type VersionedWorkflowConfig = {
  readonly schema_info: Version & { readonly schema_name: string }
  readonly data: WorkflowConfig
}

// Use strict schemas for validation

export function createWorkflowConfig({
  nodes,
  edges,
  metadata,
}: {
  readonly nodes: Node<Record<string, unknown>>[]
  readonly edges: Edge[]
  readonly metadata: WorkflowMetadata
}): WorkflowConfig {
  const serializedNodes: SerializedNode[] = nodes.map((node) => ({
    id: node.id,
    type: node.type || 'unknown',
    position: node.position,
    data: serializeNodeData(node.data),
  }))

  return {
    metadata,
    nodes: serializedNodes,
    edges,
  }
}

export function serializeWorkflow({
  reactFlowObject,
  metadata,
}: {
  readonly reactFlowObject: ReactFlowObject
  readonly metadata: WorkflowMetadata
}): VersionedWorkflowConfig {
  const workflowConfig = createWorkflowConfig({
    nodes: reactFlowObject.nodes,
    edges: reactFlowObject.edges,
    metadata,
  })

  const versionMetadata = getVersionMetadata('WorkflowConfig')

  return {
    schema_info: versionMetadata,
    data: workflowConfig,
  }
}

export function deserializeWorkflow({
  versionedConfig,
  nodeFactory,
}: {
  readonly versionedConfig: VersionedWorkflowConfig
  readonly nodeFactory: (
    nodeType: string,
    data: Record<string, unknown>
  ) => unknown
}): DeserializedWorkflowState {
  const { data } = versionedConfig

  const deserializedNodes: Node<Record<string, unknown>>[] = data.nodes.map(
    (serializedNode) => ({
      id: serializedNode.id,
      type: serializedNode.type,
      position: serializedNode.position,
      data: deserializeNodeData({
        nodeType: serializedNode.data.nodeType,
        serializedData: serializedNode.data.serializedData,
        nodeFactory,
      }) as Record<string, unknown>,
    })
  )

  return {
    nodes: deserializedNodes,
    edges: data.edges,
    metadata: data.metadata,
  }
}

export function validateWorkflowConfig({
  config,
}: {
  readonly config: unknown
}): ValidationResult {
  try {
    StrictWorkflowConfigSchema.parse(config)
    return {
      isValid: true,
      errors: [],
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors = error.issues.map((issue) => {
        const path = issue.path.join('.')
        return `${path}: ${issue.message}`
      })
      return {
        isValid: false,
        errors,
      }
    }

    return {
      isValid: false,
      errors: ['Unknown validation error'],
    }
  }
}

export function validateVersionedWorkflowConfig({
  versionedConfig,
}: {
  readonly versionedConfig: unknown
}): ValidationResult {
  try {
    StrictVersionedWorkflowConfigSchema.parse(versionedConfig)
    return {
      isValid: true,
      errors: [],
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors = error.issues.map((issue) => {
        const path = issue.path.join('.')
        return `${path}: ${issue.message}`
      })
      return {
        isValid: false,
        errors,
      }
    }

    return {
      isValid: false,
      errors: ['Unknown validation error'],
    }
  }
}

export function serializeFromReactFlowObject({
  toObjectResult,
  metadata,
}: {
  readonly toObjectResult: ReactFlowObject
  readonly metadata: WorkflowMetadata
}): VersionedWorkflowConfig {
  return serializeWorkflow({
    reactFlowObject: toObjectResult,
    metadata,
  })
}

export function prepareForReactFlow({
  versionedConfig,
  nodeFactory,
}: {
  readonly versionedConfig: VersionedWorkflowConfig
  readonly nodeFactory: (
    nodeType: string,
    data: Record<string, unknown>
  ) => unknown
}): DeserializedWorkflowState {
  return deserializeWorkflow({ versionedConfig, nodeFactory })
}

export function createNodeFactory(): (
  nodeType: string,
  data: Record<string, unknown>
) => unknown {
  return function nodeFactory(
    nodeType: string,
    data: Record<string, unknown>
  ): unknown {
    switch (nodeType) {
      // Logic nodes (constructor names)
      case 'ConstantNode':
        const constantMetadata = data.metadata as ConstantNodeMetadata
        return factory.createConstantNode({
          label: data.label as string,
          value: constantMetadata?.value,
          valueType: constantMetadata?.valueType,
          id: data.id as string,
        })
      // Logic nodes (enum string values)
      case 'constant':
        return factory.createConstantNode({
          label: data.label as string,
          value: (data.metadata as ConstantNodeMetadata)?.value,
          valueType: (data.metadata as ConstantNodeMetadata)?.valueType,
          id: data.id as string,
        })
      case 'CalculationNode':
        const calcMetadata = data.metadata as {
          operation: CalculationOperation
        }
        return factory.createCalculationNode({
          label: data.label as string,
          operation: calcMetadata?.operation,
          id: data.id as string,
        })
      case 'calculation':
        return factory.createCalculationNode({
          label: data.label as string,
          operation: (data.metadata as { operation: CalculationOperation })
            ?.operation,
          id: data.id as string,
        })
      case 'ComparisonNode':
        const compMetadata = data.metadata as { operation: ComparisonOperation }
        return factory.createComparisonNode({
          label: data.label as string,
          operation: compMetadata?.operation,
          id: data.id as string,
        })
      case 'comparison':
        return factory.createComparisonNode({
          label: data.label as string,
          operation: (data.metadata as { operation: ComparisonOperation })
            ?.operation,
          id: data.id as string,
        })
      case 'WriteSetpointNode':
        const writeMetadata = data.metadata as { priority: number }
        return factory.createWriteSetpointNode({
          label: data.label as string,
          priority: writeMetadata?.priority,
          id: data.id as string,
        })
      case 'write-setpoint':
        return factory.createWriteSetpointNode({
          label: data.label as string,
          priority: (data.metadata as { priority: number })?.priority,
          id: data.id as string,
        })
      case 'SwitchNode':
        const switchMetadata = data.metadata as SwitchNodeMetadata
        return factory.createSwitchNode({
          label: data.label as string,
          condition: switchMetadata?.condition,
          threshold: switchMetadata?.threshold,
          activeLabel: switchMetadata?.activeLabel,
          inactiveLabel: switchMetadata?.inactiveLabel,
          id: data.id as string,
        })
      case 'switch':
        const switchMeta = data.metadata as SwitchNodeMetadata
        return factory.createSwitchNode({
          label: data.label as string,
          condition: switchMeta?.condition,
          threshold: switchMeta?.threshold,
          activeLabel: switchMeta?.activeLabel,
          inactiveLabel: switchMeta?.inactiveLabel,
          id: data.id as string,
        })
      case 'TimerNode':
        const timerMetadata = data.metadata as { duration: number }
        return factory.createTimerNode({
          label: data.label as string,
          duration: timerMetadata?.duration,
          id: data.id as string,
        })
      case 'timer':
        const timerMeta = data.metadata as TimerNodeMetadata
        return factory.createTimerNode({
          label: data.label as string,
          duration: timerMeta?.duration,
          id: data.id as string,
        })
      case 'ScheduleNode':
        const scheduleMetadata = data.metadata as {
          startTime: string
          endTime: string
          days: string[]
        }
        return factory.createScheduleNode({
          label: data.label as string,
          startTime: scheduleMetadata?.startTime,
          endTime: scheduleMetadata?.endTime,
          days: scheduleMetadata?.days as DayOfWeek[],
          id: data.id as string,
        })
      case 'schedule':
        const scheduleMeta = data.metadata as ScheduleNodeMetadata
        return factory.createScheduleNode({
          label: data.label as string,
          startTime: scheduleMeta?.startTime,
          endTime: scheduleMeta?.endTime,
          days: scheduleMeta?.days as DayOfWeek[],
          id: data.id as string,
        })
      case 'FunctionNode':
        const functionMetadata = data.metadata as {
          code: string
          inputs: { id: string; label: string }[]
          timeout: number
        }
        return factory.createFunctionNode({
          label: data.label as string,
          code: functionMetadata?.code,
          inputs: functionMetadata?.inputs,
          timeout: functionMetadata?.timeout,
          id: data.id as string,
        })
      case 'function':
        const fnMeta = data.metadata as FunctionNodeMetadata
        return factory.createFunctionNode({
          label: data.label as string,
          code: fnMeta?.code,
          inputs: fnMeta?.inputs,
          timeout: fnMeta?.timeout,
          id: data.id as string,
        })
      // BACnet nodes (constructor names)
      case 'AnalogInputNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      // BACnet nodes (enum string values)
      case 'analog-input':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'AnalogOutputNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'analog-output':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'AnalogValueNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'analog-value':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'BinaryInputNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'binary-input':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'BinaryOutputNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'binary-output':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'BinaryValueNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'binary-value':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'MultistateInputNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'multistate-input':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'MultistateOutputNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'multistate-output':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'MultistateValueNode':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      case 'multistate-value':
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
        })
      default:
        throw new Error(`Unknown node type: ${nodeType}`)
    }
  }
}
