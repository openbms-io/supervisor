import { z } from 'zod'
import { Node, Edge } from '@xyflow/react'
import { withVersion, getVersionMetadata, type Version } from 'bms-schemas'
import {
  serializeNodeData,
  deserializeNodeData,
  type SerializedNodeData,
} from './node-serializer'
import factory from '@/lib/data-nodes/factory'
import { type ConstantNodeMetadata } from '@/lib/data-nodes/constant-node'
import { type CalculationOperation } from '@/lib/data-nodes/calculation-node'
import { type ComparisonOperation } from '@/lib/data-nodes/comparison-node'
import { type DayOfWeek } from '@/lib/data-nodes/schedule-node'

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

const WorkflowMetadataSchema = z.object({
  lastModified: z.string().datetime(),
  createdBy: z.string().optional(),
  description: z.string().optional(),
})

const SerializedNodeDataSchema = z.object({
  nodeType: z.string(),
  serializedData: z.record(z.unknown()),
})

const SerializedNodeSchema = z.object({
  id: z.string(),
  type: z.string(),
  position: z.object({
    x: z.number(),
    y: z.number(),
  }),
  data: SerializedNodeDataSchema,
})

const WorkflowConfigBaseSchema = z.object({
  metadata: WorkflowMetadataSchema,
  nodes: z.array(SerializedNodeSchema),
  edges: z.array(z.any()),
})

const WorkflowConfigSchema = withVersion(
  WorkflowConfigBaseSchema,
  'WorkflowConfig'
)

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
    WorkflowConfigBaseSchema.parse(config)
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
    WorkflowConfigSchema.parse(versionedConfig)
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
      case 'ConstantNode':
        const constantMetadata = data.metadata as ConstantNodeMetadata
        return factory.createConstantNode({
          label: data.label as string,
          value: constantMetadata?.value,
          valueType: constantMetadata?.valueType,
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
      case 'ComparisonNode':
        const compMetadata = data.metadata as { operation: ComparisonOperation }
        return factory.createComparisonNode({
          label: data.label as string,
          operation: compMetadata?.operation,
          id: data.id as string,
        })
      case 'WriteSetpointNode':
        const writeMetadata = data.metadata as { priority: number }
        return factory.createWriteSetpointNode({
          label: data.label as string,
          priority: writeMetadata?.priority,
          id: data.id as string,
        })
      case 'SwitchNode':
        const switchMetadata = data.metadata as {
          condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
          threshold: number
          activeLabel: string
          inactiveLabel: string
        }
        return factory.createSwitchNode({
          label: data.label as string,
          condition: switchMetadata?.condition,
          threshold: switchMetadata?.threshold,
          activeLabel: switchMetadata?.activeLabel,
          inactiveLabel: switchMetadata?.inactiveLabel,
          id: data.id as string,
        })
      case 'TimerNode':
        const timerMetadata = data.metadata as { duration: number }
        return factory.createTimerNode({
          label: data.label as string,
          duration: timerMetadata?.duration,
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
      case 'AnalogInputNode':
        const analogInputMetadata = data.metadata as {
          pointId: string
          objectType: 'analog-input'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: analogInputMetadata.pointId,
            objectType: analogInputMetadata.objectType,
            objectId: analogInputMetadata.objectId,
            supervisorId: analogInputMetadata.supervisorId,
            controllerId: analogInputMetadata.controllerId,
            name: analogInputMetadata.name,
            discoveredProperties: analogInputMetadata.discoveredProperties,
            position: analogInputMetadata.position,
          },
          id: data.id as string,
        })
      case 'AnalogOutputNode':
        const analogOutputMetadata = data.metadata as {
          pointId: string
          objectType: 'analog-output'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: analogOutputMetadata.pointId,
            objectType: analogOutputMetadata.objectType,
            objectId: analogOutputMetadata.objectId,
            supervisorId: analogOutputMetadata.supervisorId,
            controllerId: analogOutputMetadata.controllerId,
            name: analogOutputMetadata.name,
            discoveredProperties: analogOutputMetadata.discoveredProperties,
            position: analogOutputMetadata.position,
          },
          id: data.id as string,
        })
      case 'AnalogValueNode':
        const analogValueMetadata = data.metadata as {
          pointId: string
          objectType: 'analog-value'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: analogValueMetadata.pointId,
            objectType: analogValueMetadata.objectType,
            objectId: analogValueMetadata.objectId,
            supervisorId: analogValueMetadata.supervisorId,
            controllerId: analogValueMetadata.controllerId,
            name: analogValueMetadata.name,
            discoveredProperties: analogValueMetadata.discoveredProperties,
            position: analogValueMetadata.position,
          },
          id: data.id as string,
        })
      case 'BinaryInputNode':
        const binaryInputMetadata = data.metadata as {
          pointId: string
          objectType: 'binary-input'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: binaryInputMetadata.pointId,
            objectType: binaryInputMetadata.objectType,
            objectId: binaryInputMetadata.objectId,
            supervisorId: binaryInputMetadata.supervisorId,
            controllerId: binaryInputMetadata.controllerId,
            name: binaryInputMetadata.name,
            discoveredProperties: binaryInputMetadata.discoveredProperties,
            position: binaryInputMetadata.position,
          },
          id: data.id as string,
        })
      case 'BinaryOutputNode':
        const binaryOutputMetadata = data.metadata as {
          pointId: string
          objectType: 'binary-output'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: binaryOutputMetadata.pointId,
            objectType: binaryOutputMetadata.objectType,
            objectId: binaryOutputMetadata.objectId,
            supervisorId: binaryOutputMetadata.supervisorId,
            controllerId: binaryOutputMetadata.controllerId,
            name: binaryOutputMetadata.name,
            discoveredProperties: binaryOutputMetadata.discoveredProperties,
            position: binaryOutputMetadata.position,
          },
          id: data.id as string,
        })
      case 'BinaryValueNode':
        const binaryValueMetadata = data.metadata as {
          pointId: string
          objectType: 'binary-value'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: binaryValueMetadata.pointId,
            objectType: binaryValueMetadata.objectType,
            objectId: binaryValueMetadata.objectId,
            supervisorId: binaryValueMetadata.supervisorId,
            controllerId: binaryValueMetadata.controllerId,
            name: binaryValueMetadata.name,
            discoveredProperties: binaryValueMetadata.discoveredProperties,
            position: binaryValueMetadata.position,
          },
          id: data.id as string,
        })
      case 'MultistateInputNode':
        const multistateInputMetadata = data.metadata as {
          pointId: string
          objectType: 'multistate-input'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: multistateInputMetadata.pointId,
            objectType: multistateInputMetadata.objectType,
            objectId: multistateInputMetadata.objectId,
            supervisorId: multistateInputMetadata.supervisorId,
            controllerId: multistateInputMetadata.controllerId,
            name: multistateInputMetadata.name,
            discoveredProperties: multistateInputMetadata.discoveredProperties,
            position: multistateInputMetadata.position,
          },
          id: data.id as string,
        })
      case 'MultistateOutputNode':
        const multistateOutputMetadata = data.metadata as {
          pointId: string
          objectType: 'multistate-output'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: multistateOutputMetadata.pointId,
            objectType: multistateOutputMetadata.objectType,
            objectId: multistateOutputMetadata.objectId,
            supervisorId: multistateOutputMetadata.supervisorId,
            controllerId: multistateOutputMetadata.controllerId,
            name: multistateOutputMetadata.name,
            discoveredProperties: multistateOutputMetadata.discoveredProperties,
            position: multistateOutputMetadata.position,
          },
          id: data.id as string,
        })
      case 'MultistateValueNode':
        const multistateValueMetadata = data.metadata as {
          pointId: string
          objectType: 'multistate-value'
          objectId: number
          supervisorId: string
          controllerId: string
          name: string
          discoveredProperties: Record<string, unknown>
          position?: { x: number; y: number }
        }
        return factory.createDataNodeFromBacnetConfig({
          config: {
            pointId: multistateValueMetadata.pointId,
            objectType: multistateValueMetadata.objectType,
            objectId: multistateValueMetadata.objectId,
            supervisorId: multistateValueMetadata.supervisorId,
            controllerId: multistateValueMetadata.controllerId,
            name: multistateValueMetadata.name,
            discoveredProperties: multistateValueMetadata.discoveredProperties,
            position: multistateValueMetadata.position,
          },
          id: data.id as string,
        })
      default:
        throw new Error(`Unknown node type: ${nodeType}`)
    }
  }
}
