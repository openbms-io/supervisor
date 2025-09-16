import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Settings2, Loader2 } from 'lucide-react'

interface FunctionNodeHeaderProps {
  label: string
  isQuickJSReady: boolean
  initError?: string
  onSettingsClick: () => void
}

export const FunctionNodeHeader = ({
  label,
  isQuickJSReady,
  initError,
  onSettingsClick,
}: FunctionNodeHeaderProps) => {
  return (
    <>
      <Button
        size="icon"
        variant="ghost"
        className="absolute top-1 right-1 h-6 w-6"
        onClick={(e) => {
          e.stopPropagation()
          onSettingsClick()
        }}
      >
        <Settings2 className="h-3 w-3" />
      </Button>

      <div className="text-center">
        <span className="text-sm font-medium">{label}</span>
        <Badge variant="secondary" className="ml-2 text-xs">
          JS Function
        </Badge>
        {!isQuickJSReady && !initError && (
          <Loader2 className="w-3 h-3 ml-2 animate-spin inline" />
        )}
      </div>
    </>
  )
}
