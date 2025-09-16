import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Plus, Trash2 } from 'lucide-react'
import { FunctionInput } from '@/lib/data-nodes/function-node'

interface FunctionInputsManagerProps {
  inputs: FunctionInput[]
  onAddInput: () => void
  onRemoveInput: (id: string) => void
  onInputLabelChange: (id: string, newLabel: string) => void
}

export const FunctionInputsManager = ({
  inputs,
  onAddInput,
  onRemoveInput,
  onInputLabelChange,
}: FunctionInputsManagerProps) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label>Function Inputs</Label>
        <Button
          size="sm"
          variant="outline"
          onClick={onAddInput}
          className="h-8"
        >
          <Plus className="w-3 h-3 mr-1" />
          Add Input
        </Button>
      </div>

      <div className="space-y-2">
        {inputs.map((input, index) => (
          <div key={input.id} className="flex items-center gap-2">
            <div className="flex items-center gap-2 flex-1">
              <span className="text-xs text-muted-foreground w-8">
                #{index + 1}
              </span>
              <Input
                value={input.id}
                disabled
                className="w-24 font-mono text-xs bg-muted"
              />
              <Input
                value={input.label}
                onChange={(e) => onInputLabelChange(input.id, e.target.value)}
                placeholder="Display Label"
                className="flex-1"
              />
            </div>
            <Button
              size="icon"
              variant="ghost"
              onClick={() => onRemoveInput(input.id)}
              className="h-8 w-8"
              disabled={inputs.length === 1}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Input IDs (e.g., input1, input2) are used as parameter names in the
        execute function
      </p>
    </div>
  )
}
