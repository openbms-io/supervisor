import { useState, useCallback, useMemo } from 'react'
import { useFlowStore } from '@/store/use-flow-store'
import {
  FunctionInput,
  FunctionNodeMetadata,
} from '@/lib/data-nodes/function-node'
import { useFunctionSignature } from './use-function-signature'

interface UseFunctionPropertiesProps {
  nodeId: string
  onClose: () => void
}

export const useFunctionProperties = ({
  nodeId,
  onClose,
}: UseFunctionPropertiesProps) => {
  const node = useFlowStore((state) => state.nodes.find((n) => n.id === nodeId))
  const updateNode = useFlowStore((state) => state.updateNode)
  const { updateFunctionSignature } = useFunctionSignature()

  // Initialize local state from node metadata with useMemo to avoid re-creation
  const metadata = useMemo(
    () => node?.data?.metadata as FunctionNodeMetadata | undefined,
    [node?.data?.metadata]
  )

  const [code, setCode] = useState(
    metadata?.code || 'function execute(input1) {\n  return input1;\n}'
  )
  const [inputs, setInputs] = useState<FunctionInput[]>(
    metadata?.inputs || [{ id: 'input1', label: 'Input 1' }]
  )
  const [timeout, setTimeout] = useState(metadata?.timeout || 1000)
  const [showExpandedEditor, setShowExpandedEditor] = useState(false)
  const [expandedCode, setExpandedCode] = useState(
    metadata?.code || 'function execute(input1) {\n  return input1;\n}'
  )

  const handleAddInput = useCallback(() => {
    const newInputId = `input${inputs.length + 1}`
    const newInput: FunctionInput = {
      id: newInputId,
      label: `Input ${inputs.length + 1}`,
    }
    const newInputs = [...inputs, newInput]
    setInputs(newInputs)

    // Update the function signature in the code
    const updatedCode = updateFunctionSignature(newInputs, code)
    setCode(updatedCode)
    setExpandedCode(updatedCode)
  }, [inputs, code, updateFunctionSignature])

  const handleRemoveInput = useCallback(
    (id: string) => {
      const newInputs = inputs.filter((input) => input.id !== id)
      setInputs(newInputs)

      // Update the function signature in the code
      const updatedCode = updateFunctionSignature(newInputs, code)
      setCode(updatedCode)
      setExpandedCode(updatedCode)
    },
    [inputs, code, updateFunctionSignature]
  )

  const handleInputLabelChange = useCallback(
    (id: string, newLabel: string) => {
      setInputs(
        inputs.map((input) =>
          input.id === id ? { ...input, label: newLabel } : input
        )
      )
    },
    [inputs]
  )

  const handleCodeChange = useCallback((newCode: string) => {
    setCode(newCode)
  }, [])

  const handleTimeoutChange = useCallback((newTimeout: number) => {
    setTimeout(newTimeout)
  }, [])

  const handleApply = useCallback(() => {
    updateNode({
      type: 'UPDATE_FUNCTION_CONFIG',
      nodeId,
      code,
      inputs,
      timeout,
    })
    onClose()
  }, [nodeId, code, inputs, timeout, updateNode, onClose])

  const handleCancel = useCallback(() => {
    // Reset to original values
    setCode(metadata?.code || 'function execute(input1) {\n  return input1;\n}')
    setInputs(metadata?.inputs || [{ id: 'input1', label: 'Input 1' }])
    setTimeout(metadata?.timeout || 1000)
    onClose()
  }, [metadata, onClose])

  const handleExpandEditor = useCallback(() => {
    setExpandedCode(code)
    setShowExpandedEditor(true)
  }, [code])

  const handleExpandedEditorSave = useCallback(() => {
    setCode(expandedCode)
    setShowExpandedEditor(false)
  }, [expandedCode])

  const handleExpandedEditorCancel = useCallback(() => {
    setExpandedCode(code)
    setShowExpandedEditor(false)
  }, [code])

  const handleExpandedCodeChange = useCallback((newCode: string) => {
    setExpandedCode(newCode)
  }, [])

  return {
    // State
    node,
    code,
    inputs,
    timeout,
    showExpandedEditor,
    expandedCode,

    // Handlers
    handleAddInput,
    handleRemoveInput,
    handleInputLabelChange,
    handleCodeChange,
    handleTimeoutChange,
    handleApply,
    handleCancel,
    handleExpandEditor,
    handleExpandedEditorSave,
    handleExpandedEditorCancel,
    handleExpandedCodeChange,
  }
}
