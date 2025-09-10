import { BacnetObjectType } from './infrastructure'

// Define all possible property value types
export type PropertyValue = number | boolean | string | StatusFlags | null

export interface StatusFlags {
  inAlarm: boolean
  fault: boolean
  overridden: boolean
  outOfService: boolean
}

// All possible BACnet properties with their types
export interface BacnetProperties {
  presentValue?: number | boolean | string
  statusFlags?: StatusFlags
  eventState?: string
  reliability?: string
  outOfService?: boolean
  units?: string
  description?: string
  minPresValue?: number
  maxPresValue?: number
  resolution?: number
  covIncrement?: number
  timeDelay?: number
  highLimit?: number
  lowLimit?: number
  deadband?: number
  priorityArray?: number[]
  relinquishDefault?: number | boolean | string

  // Multistate-specific properties
  numberOfStates?: number // Required for multistate objects
  stateText?: (string | null)[] // Optional array of state descriptions (null at index 0 for BACnet 1-based indexing)
  // Add more as discovered from actual devices
}

// Property metadata interface
export interface PropertyMetadata {
  name: string
  readable: boolean
  writable: boolean
}

// Properties that are ALWAYS read-only regardless of object type
const ALWAYS_READONLY: Record<string, PropertyMetadata> = {
  statusFlags: { name: 'Status Flags', readable: true, writable: false },
  eventState: { name: 'Event State', readable: true, writable: false },
  reliability: { name: 'Reliability', readable: true, writable: false },
  units: { name: 'Units', readable: true, writable: false },
  description: { name: 'Description', readable: true, writable: false },
  resolution: { name: 'Resolution', readable: true, writable: false },
  priorityArray: { name: 'Priority Array', readable: true, writable: false },
}

// Properties that are ALWAYS writable regardless of object type
const ALWAYS_WRITABLE: Record<string, PropertyMetadata> = {
  outOfService: { name: 'Out of Service', readable: true, writable: true },
  covIncrement: { name: 'COV Increment', readable: true, writable: true },
  timeDelay: { name: 'Time Delay', readable: true, writable: true },
  deadband: { name: 'Deadband', readable: true, writable: true },
}

// Properties specific to analog objects only
const ANALOG_ONLY: Record<string, PropertyMetadata> = {
  minPresValue: { name: 'Min Present Value', readable: true, writable: true },
  maxPresValue: { name: 'Max Present Value', readable: true, writable: true },
  highLimit: { name: 'High Limit', readable: true, writable: true },
  lowLimit: { name: 'Low Limit', readable: true, writable: true },
}

// Properties specific to multistate objects only
const MULTISTATE_PROPERTIES: Record<string, PropertyMetadata> = {
  numberOfStates: { name: 'Number of States', readable: true, writable: false },
  stateText: { name: 'State Text', readable: true, writable: false },
}

// Object-type-specific metadata for special cases
const OBJECT_TYPE_METADATA: Record<
  BacnetObjectType,
  Record<string, PropertyMetadata>
> = {
  'analog-input': {
    presentValue: { name: 'Present Value', readable: true, writable: false },
    ...ANALOG_ONLY,
  },
  'analog-output': {
    presentValue: { name: 'Present Value', readable: true, writable: true },
    relinquishDefault: {
      name: 'Relinquish Default',
      readable: true,
      writable: true,
    },
    ...ANALOG_ONLY,
  },
  'analog-value': {
    presentValue: { name: 'Present Value', readable: true, writable: true },
    relinquishDefault: {
      name: 'Relinquish Default',
      readable: true,
      writable: true,
    },
    ...ANALOG_ONLY,
  },
  'binary-input': {
    presentValue: { name: 'Present Value', readable: true, writable: false },
  },
  'binary-output': {
    presentValue: { name: 'Present Value', readable: true, writable: true },
    relinquishDefault: {
      name: 'Relinquish Default',
      readable: true,
      writable: true,
    },
  },
  'binary-value': {
    presentValue: { name: 'Present Value', readable: true, writable: true },
    relinquishDefault: {
      name: 'Relinquish Default',
      readable: true,
      writable: true,
    },
  },
  'multistate-input': {
    presentValue: { name: 'Present Value', readable: true, writable: false },
    ...MULTISTATE_PROPERTIES,
  },
  'multistate-output': {
    presentValue: { name: 'Present Value', readable: true, writable: true },
    relinquishDefault: {
      name: 'Relinquish Default',
      readable: true,
      writable: true,
    },
    ...MULTISTATE_PROPERTIES,
  },
  'multistate-value': {
    presentValue: { name: 'Present Value', readable: true, writable: true },
    relinquishDefault: {
      name: 'Relinquish Default',
      readable: true,
      writable: true,
    },
    ...MULTISTATE_PROPERTIES,
  },
}

// Simple function - no string checks, just lookups
export function getPropertyMetadata(
  objectType: BacnetObjectType,
  propertyName: keyof BacnetProperties
): PropertyMetadata | undefined {
  const propName = propertyName as string

  // Check object-type-specific first
  if (OBJECT_TYPE_METADATA[objectType]?.[propName]) {
    return OBJECT_TYPE_METADATA[objectType][propName]
  }

  // Then check always-readonly
  if (ALWAYS_READONLY[propName]) {
    return ALWAYS_READONLY[propName]
  }

  // Then check always-writable
  if (ALWAYS_WRITABLE[propName]) {
    return ALWAYS_WRITABLE[propName]
  }

  // Property not supported for this object type
  return undefined
}
