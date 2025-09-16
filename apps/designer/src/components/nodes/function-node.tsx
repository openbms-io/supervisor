'use client'

import { memo, useState, useEffect, useCallback } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CustomHandle } from './custom-handle'
import { useFlowStore } from '@/store/use-flow-store'
import { NodeCategory, ComputeValue } from '@/types/infrastructure'
import { FunctionNodeData } from '@/types/node-data-types'
import {
  AlertCircle,
  Loader2,
  Settings2,
  ChevronRight,
  Terminal,
} from 'lucide-react'
import { getQuickJSExecutor } from '@/lib/services/quickjs-executor'
import { FunctionPropertiesContainer } from '@/containers/function-properties-container'

const EMPTY_INPUTS: ComputeValue[] = []

export const FunctionNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as FunctionNodeData
  const { label, metadata } = typedData

  const [isQuickJSReady, setQuickJSReady] = useState(false)
  const [initError, setInitError] = useState<string | undefined>()
  const [showProperties, setShowProperties] = useState(false)
  const [showConsole, setShowConsole] = useState(false)

  // Initialize QuickJS when component mounts
  useEffect(() => {
    const initializeQuickJS = async () => {
      try {
        await getQuickJSExecutor()
        setQuickJSReady(true)
      } catch (error) {
        setInitError((error as Error).message)
        console.error('Failed to initialize QuickJS:', error)
      }
    }

    initializeQuickJS()
  }, [])

  const handleDoubleClick = useCallback(() => {
    setShowProperties(true)
  }, [])

  // Get dynamic values from store
  const inputs = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.inputValues || EMPTY_INPUTS
    }
    return EMPTY_INPUTS
  })

  const result = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.computedValue
    }
    return undefined
  })

  const error = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.lastError
    }
    return undefined
  })

  // Get console logs from store
  const consoleLogs = useFlowStore((state) => {
    const node = state.nodes.find((n) => n.id === id)
    if (node?.data?.category === NodeCategory.LOGIC) {
      const logicData = node.data as FunctionNodeData
      return logicData.consoleLogs || []
    }
    return []
  })

  const formatValue = (value: ComputeValue | undefined): string => {
    if (value === undefined) return '-'
    if (typeof value === 'number') {
      return isNaN(value) ? 'NaN' : value.toFixed(2)
    }
    return value ? 'true' : 'false'
  }

  return (
    <>
      <Card
        className={`min-w-[250px] border-2 ${
          error || initError ? 'border-red-500' : 'border-purple-500'
        } relative`}
        onDoubleClick={handleDoubleClick}
      >
        {/* Settings button in top-right corner */}
        <Button
          size="icon"
          variant="ghost"
          className="absolute top-1 right-1 h-6 w-6"
          onClick={(e) => {
            e.stopPropagation()
            setShowProperties(true)
          }}
        >
          <Settings2 className="h-3 w-3" />
        </Button>

        <div className="p-3 space-y-2">
          <div className="text-center">
            <span className="text-sm font-medium">{label}</span>
            <Badge variant="secondary" className="ml-2 text-xs">
              JS Function
            </Badge>
            {!isQuickJSReady && !initError && (
              <Loader2 className="w-3 h-3 ml-2 animate-spin inline" />
            )}
          </div>

          {/* Input values display */}
          <div className="text-xs space-y-1">
            {metadata.inputs.map((input, idx) => (
              <div key={input.id} className="flex justify-between">
                <span className="text-muted-foreground">{input.label}:</span>
                <span className="font-mono">
                  {formatValue(
                    Array.isArray(inputs) && inputs.length > idx
                      ? inputs[idx]
                      : undefined
                  )}
                </span>
              </div>
            ))}
          </div>

          {/* Status and result display */}
          <div className="border-t pt-2">
            {initError ? (
              <div className="flex items-center gap-1 text-xs text-red-500">
                <AlertCircle className="w-3 h-3" />
                <span className="truncate">Init Error: {initError}</span>
              </div>
            ) : error ? (
              <div className="flex items-center gap-1 text-xs text-red-500">
                <AlertCircle className="w-3 h-3" />
                <span className="truncate">{error}</span>
              </div>
            ) : !isQuickJSReady ? (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Loading JS Engine...</span>
              </div>
            ) : (
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">Result:</span>
                <span className="text-lg font-bold text-purple-600">
                  {formatValue(result as ComputeValue | undefined)}
                </span>
              </div>
            )}
          </div>

          {/* Console Section */}
          {consoleLogs.length > 0 && (
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
          )}
        </div>

        {/* Dynamic input handles */}
        {metadata.inputs.map((input, idx) => (
          <CustomHandle
            key={input.id}
            type="target"
            position={Position.Left}
            id={input.id}
            style={{ top: `${20 + (idx * 60) / metadata.inputs.length}%` }}
            className="w-3 h-3 bg-purple-500 border-2 border-background"
            connectionCount={1}
          />
        ))}

        {/* Output handle */}
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          className="w-3 h-3 bg-purple-500 border-2 border-background"
        />
      </Card>

      {/* Properties panel */}
      <FunctionPropertiesContainer
        nodeId={id}
        isOpen={showProperties}
        onClose={() => setShowProperties(false)}
      />
    </>
  )
})

FunctionNode.displayName = 'FunctionNode'
