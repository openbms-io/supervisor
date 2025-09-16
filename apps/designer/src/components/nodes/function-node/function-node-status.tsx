import { AlertCircle, Loader2 } from 'lucide-react'
import { ComputeValue } from '@/types/infrastructure'
import { formatValue } from './utils'

interface FunctionNodeStatusProps {
  initError?: string
  error?: string
  isQuickJSReady: boolean
  result?: ComputeValue
}

export const FunctionNodeStatus = ({
  initError,
  error,
  isQuickJSReady,
  result,
}: FunctionNodeStatusProps) => {
  if (initError) {
    return (
      <div className="flex items-center gap-1 text-xs text-red-500">
        <AlertCircle className="w-3 h-3" />
        <span className="truncate">Init Error: {initError}</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-1 text-xs text-red-500">
        <AlertCircle className="w-3 h-3" />
        <span className="truncate">{error}</span>
      </div>
    )
  }

  if (!isQuickJSReady) {
    return (
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <Loader2 className="w-3 h-3 animate-spin" />
        <span>Loading JS Engine...</span>
      </div>
    )
  }

  return (
    <div className="flex justify-between items-center">
      <span className="text-xs text-muted-foreground">Result:</span>
      <span className="text-lg font-bold text-purple-600">
        {formatValue(result)}
      </span>
    </div>
  )
}
