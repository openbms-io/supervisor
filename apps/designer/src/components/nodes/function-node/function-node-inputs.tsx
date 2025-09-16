import { FunctionInput } from '@/lib/data-nodes/function-node'
import { ComputeValue } from '@/types/infrastructure'
import { formatValue } from './utils'

interface FunctionNodeInputsProps {
  inputs: FunctionInput[]
  inputValues: ComputeValue[]
}

export const FunctionNodeInputs = ({
  inputs,
  inputValues,
}: FunctionNodeInputsProps) => {
  return (
    <div className="text-xs space-y-1">
      {inputs.map((input, idx) => (
        <div key={input.id} className="flex justify-between">
          <span className="text-muted-foreground">{input.label}:</span>
          <span className="font-mono">
            {formatValue(
              Array.isArray(inputValues) && inputValues.length > idx
                ? inputValues[idx]
                : undefined
            )}
          </span>
        </div>
      ))}
    </div>
  )
}
