import { ComputeValue } from '@/types/infrastructure'

export const formatValue = (value: ComputeValue | undefined): string => {
  if (value === undefined) return '-'
  if (typeof value === 'number') {
    return isNaN(value) ? 'NaN' : value.toFixed(2)
  }
  return value ? 'true' : 'false'
}
