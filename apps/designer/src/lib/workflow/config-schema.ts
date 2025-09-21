import { z } from 'zod'
import { NodeCategory, NodeType, type EdgeData } from '@/types/infrastructure'
import type { ConstantNodeMetadata } from '@/lib/data-nodes/constant-node'
import type { CalculationOperation } from '@/lib/data-nodes/calculation-node'
import type { ComparisonOperation } from '@/lib/data-nodes/comparison-node'
import type { FunctionNodeMetadata } from '@/lib/data-nodes/function-node'
import type { TimerNodeMetadata } from '@/lib/data-nodes/timer-node'
import type {
  ScheduleNodeMetadata,
  DayOfWeek,
} from '@/lib/data-nodes/schedule-node'
import type { SwitchNodeMetadata } from '@/lib/data-nodes/switch-node'
import type { BacnetProperties, StatusFlags } from '@/types/bacnet-properties'

// Node/category enums
export const NodeTypeSchema = z.nativeEnum(NodeType)
export const NodeCategorySchema = z.nativeEnum(NodeCategory)

// BACnet property schemas (kept permissive but typed)
const StatusFlagsSchema: z.ZodType<StatusFlags> = z.object({
  inAlarm: z.boolean(),
  fault: z.boolean(),
  overridden: z.boolean(),
  outOfService: z.boolean(),
})

const BacnetPropertiesSchema: z.ZodType<BacnetProperties> = z.object({
  presentValue: z.union([z.number(), z.boolean(), z.string()]).optional(),
  statusFlags: StatusFlagsSchema.optional(),
  eventState: z.string().optional(),
  reliability: z.string().optional(),
  outOfService: z.boolean().optional(),
  units: z.string().optional(),
  description: z.string().optional(),
  minPresValue: z.number().optional(),
  maxPresValue: z.number().optional(),
  resolution: z.number().optional(),
  covIncrement: z.number().optional(),
  timeDelay: z.number().optional(),
  highLimit: z.number().optional(),
  lowLimit: z.number().optional(),
  deadband: z.number().optional(),
  priorityArray: z.array(z.number()).optional(),
  relinquishDefault: z.union([z.number(), z.boolean(), z.string()]).optional(),
  numberOfStates: z.number().optional(),
  stateText: z.array(z.union([z.string(), z.null()])).optional(),
})

// Common pieces
const PositionSchema = z.object({ x: z.number(), y: z.number() })
const BacnetObjectTypeSchema = z.enum([
  'analog-input',
  'analog-output',
  'analog-value',
  'binary-input',
  'binary-output',
  'binary-value',
  'multistate-input',
  'multistate-output',
  'multistate-value',
])

// Bacnet config schema (matches BacnetConfig)
const BacnetConfigSchema = z.object({
  pointId: z.string(),
  objectType: BacnetObjectTypeSchema,
  objectId: z.number(),
  supervisorId: z.string(),
  controllerId: z.string(),
  discoveredProperties: BacnetPropertiesSchema,
  name: z.string(),
  position: PositionSchema.optional(),
})

// Edge data schema (validates our additional data field; keeps passthrough on edges)
export const EdgeDataSchema: z.ZodType<EdgeData> = z.object({
  sourceData: z.object({
    nodeId: z.string(),
    nodeCategory: NodeCategorySchema,
    nodeType: NodeTypeSchema,
    handle: z.string().optional(),
  }),
  targetData: z.object({
    nodeId: z.string(),
    nodeCategory: NodeCategorySchema,
    nodeType: NodeTypeSchema,
    handle: z.string().optional(),
  }),
  isActive: z.boolean().optional(),
})

// Node metadata schemas per type
const ValueTypeSchema = z.enum(['number', 'boolean', 'string'])
const ConstantNodeMetadataSchema: z.ZodType<ConstantNodeMetadata> = z.object({
  value: z.union([z.number(), z.boolean(), z.string()]),
  valueType: ValueTypeSchema,
})
const CalculationOperationSchema: z.ZodType<CalculationOperation> = z.enum([
  'add',
  'subtract',
  'multiply',
  'divide',
  'average',
])
const ComparisonOperationSchema: z.ZodType<ComparisonOperation> = z.enum([
  'equals',
  'greater',
  'less',
  'greater-equal',
  'less-equal',
])
const FunctionInputSchema = z.object({ id: z.string(), label: z.string() })
const FunctionNodeMetadataSchema: z.ZodType<FunctionNodeMetadata> = z.object({
  code: z.string(),
  inputs: z.array(FunctionInputSchema),
  timeout: z.number().optional(),
})
const TimerNodeMetadataSchema: z.ZodType<TimerNodeMetadata> = z.object({
  duration: z.number(),
})
const DayOfWeekSchema: z.ZodType<DayOfWeek> = z.enum([
  'Mon',
  'Tue',
  'Wed',
  'Thu',
  'Fri',
  'Sat',
  'Sun',
])
const ScheduleNodeMetadataSchema: z.ZodType<ScheduleNodeMetadata> = z.object({
  startTime: z.string(),
  endTime: z.string(),
  days: z.array(DayOfWeekSchema),
})
const SwitchNodeMetadataSchema: z.ZodType<SwitchNodeMetadata> = z.object({
  condition: z.enum(['gt', 'lt', 'eq', 'gte', 'lte']),
  threshold: z.number(),
  activeLabel: z.string(),
  inactiveLabel: z.string(),
})

// Serialized node.data schema by node type
const SerializedNodeInnerSchema = z.discriminatedUnion('type', [
  // Logic
  z.object({
    id: z.string(),
    type: z.literal(NodeType.CONSTANT),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: ConstantNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.CALCULATION),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: z.object({ operation: CalculationOperationSchema }),
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.COMPARISON),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: z.object({ operation: ComparisonOperationSchema }),
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.FUNCTION),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: FunctionNodeMetadataSchema,
  }),

  // Control flow
  z.object({
    id: z.string(),
    type: z.literal(NodeType.SWITCH),
    category: z.literal(NodeCategory.CONTROL_FLOW),
    label: z.string(),
    metadata: SwitchNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.TIMER),
    category: z.literal(NodeCategory.CONTROL_FLOW),
    label: z.string(),
    metadata: TimerNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.SCHEDULE),
    category: z.literal(NodeCategory.CONTROL_FLOW),
    label: z.string(),
    metadata: ScheduleNodeMetadataSchema,
  }),

  // Command
  z.object({
    id: z.string(),
    type: z.literal(NodeType.WRITE_SETPOINT),
    category: z.literal(NodeCategory.COMMAND),
    label: z.string(),
    metadata: z.object({ priority: z.number() }),
  }),

  // BACnet nodes (share same metadata shape)
  ...(
    [
      NodeType.ANALOG_INPUT,
      NodeType.ANALOG_OUTPUT,
      NodeType.ANALOG_VALUE,
      NodeType.BINARY_INPUT,
      NodeType.BINARY_OUTPUT,
      NodeType.BINARY_VALUE,
      NodeType.MULTISTATE_INPUT,
      NodeType.MULTISTATE_OUTPUT,
      NodeType.MULTISTATE_VALUE,
    ] as const
  ).map((nt) =>
    z.object({
      id: z.string(),
      type: z.literal(nt),
      category: z.literal(NodeCategory.BACNET),
      label: z.string(),
      metadata: BacnetConfigSchema,
    })
  ),
])

export const SerializedNodeDataSchema = z.object({
  // Node class constructor name or enum string; keep broad during migration
  nodeType: z.string(),
  serializedData: SerializedNodeInnerSchema,
})

export const SerializedNodeSchema = z.object({
  id: z.string(),
  type: z.string(), // React Flow node type (e.g., 'logic.constant')
  position: z.object({ x: z.number(), y: z.number() }),
  data: SerializedNodeDataSchema,
})

export const WorkflowMetadataSchema = z.object({
  lastModified: z.string().datetime(),
  createdBy: z.string().optional(),
  description: z.string().optional(),
})

export const EdgeSchema = z
  .object({
    id: z.string(),
    source: z.string(),
    target: z.string(),
    sourceHandle: z.string().optional(),
    targetHandle: z.string().optional(),
    data: EdgeDataSchema.optional(),
  })
  .passthrough()

export const WorkflowConfigSchema = z.object({
  metadata: WorkflowMetadataSchema,
  nodes: z.array(SerializedNodeSchema),
  edges: z.array(EdgeSchema),
})

// schema_info shape used by bms-schemas withVersion(); keep compatible
export const VersionSchema = z.object({
  version: z.string(),
  compatibility: z.string().optional(),
  schema_name: z.literal('WorkflowConfig'),
  generated_at: z.string().datetime().optional(),
})

export const VersionedWorkflowConfigSchema = z.object({
  schema_info: VersionSchema,
  data: WorkflowConfigSchema,
})

export type ValidatedWorkflowConfig = z.infer<
  typeof VersionedWorkflowConfigSchema
>
