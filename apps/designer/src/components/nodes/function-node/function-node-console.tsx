import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { ChevronRight, Terminal } from 'lucide-react'

interface FunctionNodeConsoleProps {
  consoleLogs: string[]
}

export const FunctionNodeConsole = ({
  consoleLogs,
}: FunctionNodeConsoleProps) => {
  const [showConsole, setShowConsole] = useState(false)

  if (consoleLogs.length === 0) return null

  return (
    <div className="border-t pt-2">
      <div
        className="flex items-center justify-between cursor-pointer hover:bg-muted/50 px-1 py-0.5 rounded"
        onClick={() => setShowConsole(!showConsole)}
      >
        <div className="flex items-center gap-1">
          <ChevronRight
            className={`w-3 h-3 transition-transform ${
              showConsole ? 'rotate-90' : ''
            }`}
          />
          <Terminal className="w-3 h-3" />
          <span className="text-xs text-muted-foreground">Console</span>
          <Badge variant="secondary" className="h-4 px-1 text-[10px]">
            {consoleLogs.length}
          </Badge>
        </div>
      </div>

      {showConsole && (
        <div className="mt-1 space-y-0.5 max-h-24 overflow-y-auto">
          {consoleLogs.slice(-3).map((log, index) => {
            const isError = log.startsWith('[ERROR]')
            const isWarn = log.startsWith('[WARN]')
            return (
              <div
                key={index}
                className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                  isError
                    ? 'text-red-500 bg-red-500/10'
                    : isWarn
                      ? 'text-yellow-500 bg-yellow-500/10'
                      : 'text-muted-foreground bg-muted/30'
                }`}
              >
                {log.length > 50 ? log.substring(0, 50) + '...' : log}
              </div>
            )
          })}
          {consoleLogs.length > 3 && (
            <div className="text-[9px] text-muted-foreground px-2">
              ...and {consoleLogs.length - 3} more
            </div>
          )}
        </div>
      )}
    </div>
  )
}
