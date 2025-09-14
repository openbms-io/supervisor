import { v4 as uuidv4, v5 as uuidv5 } from 'uuid'
import { BacnetProperties } from './bacnet-properties'
import { MessageNode } from '@/lib/message-system/types'

// BACnet namespace for deterministic UUIDs
export const BACNET_NAMESPACE = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'

// Node categories
export enum NodeCategory {
  BACNET = 'bacnet',
  LOGIC = 'logic',
  COMMAND = 'command',
  CONTROL_FLOW = 'control-flow',
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

// All node types (BACnet + logic + control flow)
export type NodeTypeString =
  | BacnetObjectType
  | 'comparison'
  | 'calculation'
  | 'condition'
  | 'timer'
  | 'schedule'
  | 'write-setpoint'
  | 'constant'
  | 'switch'
  | 'gate'

export enum NodeDirection {
  INPUT = 'input',
  OUTPUT = 'output',
  BIDIRECTIONAL = 'bidirectional',
}

// Base DataNode interface with generic handle types
export interface DataNode<
  TInputHandle extends string = string,
  TOutputHandle extends string = string,
> extends MessageNode<TInputHandle, TOutputHandle> {
  readonly id: string // UUID v4 - instance ID
  readonly type: NodeTypeString
  readonly category: NodeCategory
  readonly label: string // Display label
  readonly direction: NodeDirection
  readonly metadata?: unknown
  canConnectWith(other: DataNode): boolean
  getInputHandles?(): readonly TInputHandle[]
  getOutputHandles?(): readonly TOutputHandle[]
}

// Computation value types - what logic nodes can work with
export type ComputeValue = number | boolean

// Logic node interface with clean API and typed handles
export interface LogicNode<
  TInputHandle extends string = string,
  TOutputHandle extends string = string,
> extends DataNode<TInputHandle, TOutputHandle> {
  // Clean public API
  getValue(): ComputeValue | undefined
  getInputValues?(): ComputeValue[] // Optional - for nodes that have inputs
  reset?(): void // Optional - only for nodes that compute
}

// Command node configuration
export interface CommandConfig {
  inputValue?: ComputeValue // Value received from input
  priority: number // Node's configured priority (1-16)
  writeMode: 'normal' | 'override' | 'release'
}

// CommandNode with typed handles
export interface CommandNode
  extends DataNode<CommandInputHandle, CommandOutputHandle>,
    CommandConfig {}

// Type-safe handle types for logic nodes
export type CalculationInputHandle = 'input1' | 'input2'
export type ComparisonInputHandle = 'value1' | 'value2'
export type LogicOutputHandle = 'output'

// Type-safe handle types for command nodes
export type CommandInputHandle = 'setpoint'
export type CommandOutputHandle = 'output'

// Type-safe handle types for BACnet nodes (dynamic based on properties)
export type BacnetInputHandle = BacnetPropertyKey
export type BacnetOutputHandle = BacnetPropertyKey

// Type-safe handle types for control flow nodes
export type SwitchInputHandle = 'input'
export type SwitchOutputHandle = 'active' | 'inactive'
export type TimerInputHandle = 'trigger'
export type TimerOutputHandle = 'output'
export type GateInputHandle = 'condition' | 'value'
export type GateOutputHandle = 'output'

// Control flow node interface with typed handles
export interface ControlFlowNode<
  TInputHandle extends string = string,
  TOutputHandle extends string = string,
> extends DataNode<TInputHandle, TOutputHandle> {
  readonly category: NodeCategory.CONTROL_FLOW
  readonly direction: NodeDirection.BIDIRECTIONAL

  // Clean public API
  getValue(): ComputeValue | undefined
  reset(): void
  execute(inputs: ComputeValue[]): void
  getActiveOutputHandles(): readonly TOutputHandle[]
}

// Type-safe BACnet properties (from BacnetProperties keys)
export type BacnetPropertyKey = keyof BacnetProperties

export interface EdgeData extends Record<string, unknown> {
  sourceData: {
    nodeId: string
    nodeCategory: NodeCategory
    nodeType: NodeTypeString
    handle?: string // e.g. 'presentValue', 'statusFlags', 'eventState', etc. connected to specific property
  }

  targetData: {
    nodeId: string
    nodeCategory: NodeCategory
    nodeType: NodeTypeString
    handle?: string // e.g. 'presentValue', 'statusFlags', 'eventState', etc. connected to specific property
  }
  // Control flow state - undefined means active by default
  isActive?: boolean
}

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

// BACnet nodes have dynamic inputs and outputs based on discovered properties
export interface BacnetInputOutput
  extends DataNode<BacnetInputHandle, BacnetOutputHandle>,
    BacnetConfig {}

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

// Type guard functions
export function isControlFlowNode(node: DataNode): node is ControlFlowNode {
  return node.category === NodeCategory.CONTROL_FLOW
}

export function isLogicNode(node: DataNode): node is LogicNode {
  return node.category === NodeCategory.LOGIC
}

export function isCommandNode(node: DataNode): node is CommandNode {
  return node.category === NodeCategory.COMMAND
}

export function isBacnetNode(node: DataNode): node is BacnetInputOutput {
  return node.category === NodeCategory.BACNET
}
