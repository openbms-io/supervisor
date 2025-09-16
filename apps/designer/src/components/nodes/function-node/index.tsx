'use client'

import { memo, useState, useCallback } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { CustomHandle } from '../custom-handle'
import { FunctionNodeData } from '@/types/node-data-types'
import { ComputeValue } from '@/types/infrastructure'
import { FunctionPropertiesContainer } from '@/containers/function-properties-container'

// Import sub-components
import { FunctionNodeHeader } from './function-node-header'
import { FunctionNodeInputs } from './function-node-inputs'
import { FunctionNodeStatus } from './function-node-status'
import { FunctionNodeConsole } from './function-node-console'

// Import custom hooks
import { useFunctionNodeQuickJS } from './hooks/use-function-node-quickjs'
import { useFunctionNodeData } from './hooks/use-function-node-data'

export const FunctionNode = memo(({ data, id }: NodeProps) => {
  const typedData = data as FunctionNodeData
  const { label, metadata } = typedData

  const [showProperties, setShowProperties] = useState(false)

  // Use custom hooks
  const { isQuickJSReady, initError } = useFunctionNodeQuickJS()
  const { inputs, result, error, consoleLogs } = useFunctionNodeData(id)

  const handleDoubleClick = useCallback(() => {
    setShowProperties(true)
  }, [])

  const handleSettingsClick = useCallback(() => {
    setShowProperties(true)
  }, [])

  return (
    <>
      <Card
        className={`min-w-[250px] border-2 ${
          error || initError ? 'border-red-500' : 'border-purple-500'
        } relative`}
        onDoubleClick={handleDoubleClick}
      >
        <div className="p-3 space-y-2">
          <FunctionNodeHeader
            label={label}
            isQuickJSReady={isQuickJSReady}
            initError={initError}
            onSettingsClick={handleSettingsClick}
          />

          <FunctionNodeInputs
            inputs={metadata.inputs}
            inputValues={inputs as ComputeValue[]}
          />

          <div className="border-t pt-2">
            <FunctionNodeStatus
              initError={initError}
              error={error}
              isQuickJSReady={isQuickJSReady}
              result={result as ComputeValue | undefined}
            />
          </div>

          <FunctionNodeConsole consoleLogs={consoleLogs} />
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
