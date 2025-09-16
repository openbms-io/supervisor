'use client'

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useFunctionProperties } from './hooks/use-function-properties'

// Import components
import { FunctionPropertiesHeader } from './components/function-properties-header'
import { FunctionCodeEditor } from './components/function-code-editor'
import { FunctionInputsManager } from './components/function-inputs-manager'
import { FunctionTimeoutConfig } from './components/function-timeout-config'
import { FunctionExpandedEditor } from './components/function-expanded-editor'

interface FunctionPropertiesContainerProps {
  nodeId: string
  isOpen: boolean
  onClose: () => void
}

export function FunctionPropertiesContainer({
  nodeId,
  isOpen,
  onClose,
}: FunctionPropertiesContainerProps) {
  const {
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
  } = useFunctionProperties({ nodeId, onClose })

  if (!node) return null

  return (
    <>
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent className="w-[400px] sm:w-[540px]">
          <SheetHeader>
            <SheetTitle>
              <FunctionPropertiesHeader
                nodeLabel={node.data?.label || 'Function'}
                inputs={inputs}
              />
            </SheetTitle>
          </SheetHeader>

          <ScrollArea className="h-[calc(100vh-240px)] mt-6">
            <div className="space-y-6 pr-6 pb-4">
              <FunctionCodeEditor
                code={code}
                onCodeChange={handleCodeChange}
                onExpandEditor={handleExpandEditor}
              />

              <FunctionInputsManager
                inputs={inputs}
                onAddInput={handleAddInput}
                onRemoveInput={handleRemoveInput}
                onInputLabelChange={handleInputLabelChange}
              />

              <FunctionTimeoutConfig
                timeout={timeout}
                onTimeoutChange={handleTimeoutChange}
              />
            </div>
          </ScrollArea>

          <SheetFooter className="absolute bottom-0 left-0 right-0 p-6 bg-background border-t">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button onClick={handleApply}>Apply Changes</Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <FunctionExpandedEditor
        isOpen={showExpandedEditor}
        nodeLabel={node.data?.label || 'Function'}
        code={expandedCode}
        onCodeChange={handleExpandedCodeChange}
        onSave={handleExpandedEditorSave}
        onCancel={handleExpandedEditorCancel}
      />
    </>
  )
}
