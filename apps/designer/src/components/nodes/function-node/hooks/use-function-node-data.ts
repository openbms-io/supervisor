import { useFlowStore } from '@/store/use-flow-store'
import { NodeCategory, ComputeValue } from '@/types/infrastructure'
import { FunctionNodeData } from '@/types/node-data-types'

const EMPTY_INPUTS: ComputeValue[] = []

export const useFunctionNodeData = (nodeId: string) => {
  const inputs = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === nodeId)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.inputValues || EMPTY_INPUTS
    }
    return EMPTY_INPUTS
  })

  const result = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === nodeId)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.computedValue
    }
    return undefined
  })

  const error = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === nodeId)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.lastError
    }
    return undefined
  })

  const consoleLogs = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === nodeId)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.consoleLogs || []
    }
    return []
  })

  return { inputs, result, error, consoleLogs }
}
