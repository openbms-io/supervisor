import type { NodeType, NodeCategory } from '@/types/infrastructure'

export type SerializedEnvelope<
  M,
  T extends NodeType,
  C extends NodeCategory,
> = {
  id: string
  type: T
  category: C
  label: string
  metadata: M
}

export function makeSerializable<M, T extends NodeType, C extends NodeCategory>(
  payload: SerializedEnvelope<M, T, C>
): Record<string, unknown> {
  return payload
}
