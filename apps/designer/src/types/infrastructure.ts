import { v4 as uuidv4, v5 as uuidv5 } from 'uuid'

// BACnet namespace for deterministic UUIDs
export const BACNET_NAMESPACE = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'

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

export enum NodeDirection {
  INPUT = 'input',
  OUTPUT = 'output',
  BIDIRECTIONAL = 'bidirectional',
}

// Base DataNode interface (no pointId here)
export interface DataNode {
  readonly id: string // UUID v4 - instance ID
  readonly type: NodeTypeString
  readonly label: string // Display label
  readonly direction: NodeDirection
  readonly metadata?: unknown
  canConnectWith(other: DataNode): boolean
}

// BACnet configuration (pointId here for deterministic business ID)
export interface BacnetConfig {
  // Identification
  pointId: string // UUID v5 - deterministic business ID
  objectType: BacnetObjectType
  objectId: number
  supervisorId: string
  controllerId: string

  // BACnet properties
  presentValue: number | boolean | string
  units?: string
  description: string
  reliability: string
  statusFlags: {
    inAlarm: boolean
    fault: boolean
    overridden: boolean
    outOfService: boolean
  }

  // Display
  name: string // Point name/description
  position?: { x: number; y: number }

  // Optional limits
  minValue?: number
  maxValue?: number
}

// Composition pattern - merges BacnetConfig with DataNode behavior
export interface BacnetInputOutput
  extends BacnetConfig,
    Omit<DataNode, 'label'> {
  // label comes from BacnetConfig, rest from DataNode
}

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
