import { BacnetProperties } from '@/types/bacnet-properties'
import { ComputeValue } from '@/types/infrastructure'

/**
 * Prepares discovered properties for multistate objects by converting
 * stateText array to 1-based indexing per BACnet specification.
 *
 * BACnet multistate values are 1-indexed, so we add null at index 0
 * to allow direct array access: stateText[1] = first state
 *
 * @param properties - The discovered properties from BACnet device
 * @returns Properties with stateText converted to 1-based indexing
 */
export function prepareMultistateProperties(
  properties: BacnetProperties
): BacnetProperties {
  const prepared = { ...properties }

  // Convert stateText to 1-indexed if present
  if (prepared.stateText && Array.isArray(prepared.stateText)) {
    // Add null at index 0 for BACnet 1-based indexing
    prepared.stateText = [null, ...prepared.stateText]
  }

  return prepared
}

/**
 * Convert a BACnet property value to a ComputeValue for message passing
 */
export function convertToComputeValue(
  value: unknown
): ComputeValue | undefined {
  if (typeof value === 'number') return value
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') {
    const num = Number(value)
    return !isNaN(num) ? num : undefined
  }
  return undefined
}
