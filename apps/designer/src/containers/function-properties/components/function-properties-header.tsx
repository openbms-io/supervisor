import { Badge } from '@/components/ui/badge'
import { Code } from 'lucide-react'
import { FunctionInput } from '@/lib/data-nodes/function-node'

interface FunctionPropertiesHeaderProps {
  nodeLabel: string
  inputs: FunctionInput[]
}

export const FunctionPropertiesHeader = ({
  nodeLabel,
  inputs,
}: FunctionPropertiesHeaderProps) => {
  return (
    <div>
      <h2 className="text-lg font-semibold">{nodeLabel} Properties</h2>
      <div className="flex items-center gap-2 mt-2">
        <Badge variant="outline" className="w-fit">
          <Code className="w-3 h-3 mr-1" />
          JS Function
        </Badge>
        <Badge variant="secondary" className="w-fit">
          {inputs.length} input{inputs.length !== 1 ? 's' : ''}
        </Badge>
      </div>
    </div>
  )
}
