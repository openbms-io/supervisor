import { useCallback } from 'react'
import { FunctionInput } from '@/lib/data-nodes/function-node'

export const useFunctionSignature = () => {
  const updateFunctionSignature = useCallback(
    (newInputs: FunctionInput[], currentCode: string): string => {
      // Generate the new parameter list
      const params = newInputs.map((input) => input.id).join(', ')

      // Regular expression to match the function signature
      const functionRegex = /function\s+execute\s*\([^)]*\)/

      // Check if the function exists in the code
      if (functionRegex.test(currentCode)) {
        // Replace the existing function signature
        return currentCode.replace(functionRegex, `function execute(${params})`)
      } else {
        // If no function exists, create a default one
        return `function execute(${params}) {
  // Your code here
  return ${newInputs[0]?.id || 'null'};
}`
      }
    },
    []
  )

  return { updateFunctionSignature }
}
