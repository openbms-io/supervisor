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

// Helper to extract property name from handle ID
// Handle format: "{propertyName}$input" or "{propertyName}$output"
// We use $ delimiter because property names may contain dashes (e.g., "min-pres-value")
export function extractPropertyFromHandle(handleId: string): string | null {
  const parts = handleId.split('$')
  if (parts.length === 2 && (parts[1] === 'input' || parts[1] === 'output')) {
    return parts[0] // Return the property name part
  }
  return null // Not a BACnet handle format
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

// Composition pattern - merges BacnetConfig with DataNode behavior
export interface BacnetInputOutput extends DataNode, BacnetConfig {}

// Infrastructure types (direct references, not IDs)
export interface Supervisor {
  id: string
  name: string
  status: 'active' | 'inactive'
  controllers: Controller[] // Direct reference, not IDs!
}

export interface Controller {
  id: string
  supervisorId: string // Keep for reference
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

// UUID utilities
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
