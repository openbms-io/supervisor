import { useState, useEffect } from 'react'
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

  const functionNodeInstance = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === nodeId)
    if (node?.data?.category === NodeCategory.LOGIC) {
      return node.data as FunctionNodeData
    }
    return null
  })

  // Local state for execution results (updated via callback)
  const [result, setResult] = useState<ComputeValue | undefined>(undefined)
  const [error, setError] = useState<string | undefined>(undefined)
  const [consoleLogs, setConsoleLogs] = useState<string[]>([])

  useEffect(() => {
    if (functionNodeInstance) {
      functionNodeInstance.stateDidChange = (stateData) => {
        setResult(stateData.result)
        setError(stateData.error)
        setConsoleLogs(stateData.consoleLogs)
      }

      setResult(functionNodeInstance.computedValue)
      setError(functionNodeInstance.lastError)
      setConsoleLogs(functionNodeInstance.consoleLogs || [])

      return () => {
        functionNodeInstance.stateDidChange = undefined
      }
    }
  }, [functionNodeInstance])

  return { inputs, result, error, consoleLogs }
}
