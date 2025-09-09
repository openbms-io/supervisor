import { v4 as uuidv4, v5 as uuidv5 } from 'uuid'
import { BacnetProperties } from './bacnet-properties'

// BACnet namespace for deterministic UUIDs
export const BACNET_NAMESPACE = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'

// Node categories
export enum NodeCategory {
  BACNET = 'bacnet',
  LOGIC = 'logic',
  COMMAND = 'command',
}

// BACnet object types (bacpypes3/BAC0 naming)
export type BacnetObjectType =
  | 'analog-input'
  | 'analog-output'
  | 'analog-value'
  | 'binary-input'
  | 'binary-output'
  | 'binary-value'
  | 'multistate-input'
  | 'multistate-output'
  | 'multistate-value'

// All node types (BACnet + logic)
export type NodeTypeString =
  | BacnetObjectType
  | 'comparison'
  | 'calculation'
  | 'condition'
  | 'timer'
  | 'schedule'
  | 'write-setpoint'
  | 'constant'

export enum NodeDirection {
  INPUT = 'input',
  OUTPUT = 'output',
  BIDIRECTIONAL = 'bidirectional',
}

// Base DataNode interface (no pointId here)
export interface DataNode {
  readonly id: string // UUID v4 - instance ID
  readonly type: NodeTypeString
  readonly category: NodeCategory
  readonly label: string // Display label
  readonly direction: NodeDirection
  readonly metadata?: unknown
  canConnectWith(other: DataNode): boolean
}

// Computation value types - what logic nodes can work with
export type ComputeValue = number | boolean

// Logic node configuration (only for nodes that compute)
export interface LogicConfig {
  inputValues: ComputeValue[] // Current input values
  computedValue?: ComputeValue // Result of computation
  lastComputed?: Date

  // Only nodes with inputs have execute
  execute?(inputs: ComputeValue[]): ComputeValue
}

// LogicNode extends DataNode with computation capabilities
export interface LogicNode extends DataNode, LogicConfig {}

// Command node configuration
export interface CommandConfig {
  receivedValue?: ComputeValue
  targetPropertyName?: string
  targetNodeId?: string
}

export interface CommandNode extends DataNode, CommandConfig {}

export type EdgeCategory = NodeCategory

// Type-safe handle types for logic nodes
export type CalculationInputHandle = 'input1' | 'input2'
export type ComparisonInputHandle = 'value1' | 'value2'
export type LogicOutputHandle = 'output'

// Type-safe BACnet properties (from BacnetProperties keys)
export type BacnetPropertyKey = keyof BacnetProperties

// Category-specific edge metadata with type safety
export interface BacnetEdgeMetadata {
  sourceProperty: BacnetPropertyKey
  targetProperty: BacnetPropertyKey
}

export interface LogicEdgeMetadata {
  sourceHandle: LogicOutputHandle
  targetHandle: CalculationInputHandle | ComparisonInputHandle | string
}

export interface CommandEdgeMetadata {
  commandType: 'write' | 'override' | 'release'
  targetProperty: BacnetPropertyKey
}

// Main EdgeData type with discriminated union
export type EdgeData =
  | { category: NodeCategory.BACNET; metadata: BacnetEdgeMetadata }
  | { category: NodeCategory.LOGIC; metadata: LogicEdgeMetadata }
  | { category: NodeCategory.COMMAND; metadata: CommandEdgeMetadata }

// Single source of truth: derive valid properties from BacnetProperties interface
// This array must match the keys defined in BacnetProperties interface
const BACNET_PROPERTY_KEYS = [
  'presentValue',
  'statusFlags',
  'eventState',
  'reliability',
  'outOfService',
  'units',
  'description',
  'minPresValue',
  'maxPresValue',
  'resolution',
  'covIncrement',
  'timeDelay',
  'highLimit',
  'lowLimit',
  'deadband',
  'priorityArray',
  'relinquishDefault',
  'numberOfStates',
  'stateText',
] as const satisfies readonly (keyof BacnetProperties)[]

// Use Set for O(1) lookup performance
const BACNET_PROPERTY_SET = new Set<string>(BACNET_PROPERTY_KEYS)

// Type guard for BACnet properties
export function isBacnetProperty(
  property: string
): property is BacnetPropertyKey {
  return BACNET_PROPERTY_SET.has(property)
}

// BACnet configuration (pointId here for deterministic business ID)
export interface BacnetConfig {
  // Identification
  pointId: string // UUID v5 - deterministic business ID
  objectType: BacnetObjectType
  objectId: number
  supervisorId: string
  controllerId: string

  // All BACnet properties are now discovered
  discoveredProperties: BacnetProperties

  // Display
  name: string // Point name/description
  position?: { x: number; y: number }
}

export interface BacnetInputOutput extends DataNode, BacnetConfig {}

export interface Supervisor {
  id: string
  name: string
  status: 'active' | 'inactive'
  controllers: Controller[]
}

export interface Controller {
  id: string
  supervisorId: string
  ipAddress: string
  name: string
  status: 'connected' | 'disconnected' | 'discovering'
  discoveredPoints: BacnetConfig[] // Direct BacnetConfig array
  lastDiscovered?: Date
}

// Tree view types
export interface TreeNode {
  id: string
  type: 'supervisor' | 'controller' | 'point-group' | 'point'
  label: string
  sublabel?: string
  icon: string
  depth: number
  hasChildren: boolean
  isExpanded: boolean
  data: Supervisor | Controller | PointGroup | BacnetConfig
  children?: TreeNode[]
}

export interface PointGroup {
  objectType: BacnetObjectType
  count: number
  points: BacnetConfig[]
}

export function generateBACnetPointId({
  supervisorId,
  controllerId,
  objectId,
}: {
  supervisorId: string
  controllerId: string
  objectId: number
}): string {
  const name = `${supervisorId}:${controllerId}:${objectId}`
  return uuidv5(name, BACNET_NAMESPACE)
}

export function generateInstanceId(): string {
  return uuidv4()
}
