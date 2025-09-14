import { ComputeValue } from '@/types/infrastructure'

// Special node ID for system-triggered messages
export const ROOT_TRIGGER_NODE_ID = 'root' as const

export interface Message {
  payload: ComputeValue | undefined
  _msgid: string
  timestamp: number
  metadata?: Record<string, unknown>
}

export interface MessageNode<
  TInputHandle extends string,
  TOutputHandle extends string,
> {
  setSendCallback(callback: SendCallback<TOutputHandle>): void
  receive(
    message: Message,
    handle: TInputHandle,
    fromNodeId: string
  ): Promise<void>
}

export type SendCallback<TOutputHandle extends string> = (
  message: Message,
  nodeId: string,
  handle: TOutputHandle
) => Promise<void>
