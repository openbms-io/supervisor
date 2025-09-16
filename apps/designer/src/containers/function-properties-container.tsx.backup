'use client'

import { useState, useCallback, useMemo } from 'react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import Editor from '@monaco-editor/react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Plus, Trash2, Code, Maximize2 } from 'lucide-react'
import { FunctionInput } from '@/lib/data-nodes/function-node'
import { useFlowStore } from '@/store/use-flow-store'
import { Badge } from '@/components/ui/badge'

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
  const node = useFlowStore((state) => state.nodes.find((n) => n.id === nodeId))

  const updateNode = useFlowStore((state) => state.updateNode)

  // Initialize local state from node metadata with useMemo to avoid re-creation
  const metadata = useMemo(
    () =>
      node?.data?.metadata || {
        code: 'function execute(input1) {\n  return input1;\n}',
        inputs: [{ id: 'input1', label: 'Input 1' }],
        timeout: 1000,
      },
    [node?.data?.metadata]
  )

  const [code, setCode] = useState(metadata.code)
  const [inputs, setInputs] = useState<FunctionInput[]>(metadata.inputs)
  const [timeout, setTimeout] = useState(metadata.timeout || 1000)
  const [showExpandedEditor, setShowExpandedEditor] = useState(false)
  const [expandedCode, setExpandedCode] = useState(code)

  // Utility function to update function signature
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

  const handleAddInput = useCallback(() => {
    const newInputId = `input${inputs.length + 1}`
    const newInput: FunctionInput = {
      id: newInputId,
      label: `Input ${inputs.length + 1}`,
    }
    const newInputs = [...inputs, newInput]
    setInputs(newInputs)

    // Update the function signature in the code
    const updatedCode = updateFunctionSignature(newInputs, code)
    setCode(updatedCode)
    setExpandedCode(updatedCode)
  }, [inputs, code, updateFunctionSignature])

  const handleRemoveInput = useCallback(
    (id: string) => {
      const newInputs = inputs.filter((input) => input.id !== id)
      setInputs(newInputs)

      // Update the function signature in the code
      const updatedCode = updateFunctionSignature(newInputs, code)
      setCode(updatedCode)
      setExpandedCode(updatedCode)
    },
    [inputs, code, updateFunctionSignature]
  )

  const handleInputLabelChange = useCallback(
    (id: string, newLabel: string) => {
      setInputs(
        inputs.map((input) =>
          input.id === id ? { ...input, label: newLabel } : input
        )
      )
    },
    [inputs]
  )

  const handleApply = useCallback(() => {
    // Update the node with new metadata
    updateNode({
      type: 'UPDATE_FUNCTION_CONFIG',
      nodeId,
      code,
      inputs,
      timeout,
    })
    onClose()
  }, [nodeId, code, inputs, timeout, updateNode, onClose])

  const handleCancel = useCallback(() => {
    // Reset to original values
    setCode(metadata.code)
    setInputs(metadata.inputs)
    setTimeout(metadata.timeout || 1000)
    onClose()
  }, [metadata, onClose])

  const handleExpandEditor = useCallback(() => {
    setExpandedCode(code)
    setShowExpandedEditor(true)
  }, [code])

  const handleExpandedEditorSave = useCallback(() => {
    setCode(expandedCode)
    setShowExpandedEditor(false)
  }, [expandedCode])

  const handleExpandedEditorCancel = useCallback(() => {
    setExpandedCode(code)
    setShowExpandedEditor(false)
  }, [code])

  if (!node) return null

  return (
    <>
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent className="w-[400px] sm:w-[540px]">
          <SheetHeader>
            <SheetTitle>{node.data?.label || 'Function'} Properties</SheetTitle>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="w-fit">
                <Code className="w-3 h-3 mr-1" />
                JS Function
              </Badge>
              <Badge variant="secondary" className="w-fit">
                {inputs.length} input{inputs.length !== 1 ? 's' : ''}
              </Badge>
            </div>
          </SheetHeader>

          <ScrollArea className="h-[calc(100vh-240px)] mt-6">
            <div className="space-y-6 pr-6 pb-4">
              {/* Code Editor Section */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="code">JavaScript Code</Label>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleExpandEditor}
                    className="h-8"
                  >
                    <Maximize2 className="w-3 h-3 mr-1" />
                    Expand
                  </Button>
                </div>
                <div className="border rounded-md overflow-hidden">
                  <Editor
                    height="250px"
                    defaultLanguage="javascript"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    theme="vs-dark"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      tabSize: 2,
                      insertSpaces: true,
                      wordWrap: 'on',
                      contextmenu: false,
                      folding: false,
                      lineDecorationsWidth: 10,
                      lineNumbersMinChars: 3,
                      glyphMargin: false,
                    }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Define a function named &apos;execute&apos; that takes the
                  inputs as parameters and returns a value
                </p>
              </div>

              {/* Inputs Management Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Function Inputs</Label>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleAddInput}
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
                          onChange={(e) =>
                            handleInputLabelChange(input.id, e.target.value)
                          }
                          placeholder="Display Label"
                          className="flex-1"
                        />
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => handleRemoveInput(input.id)}
                        className="h-8 w-8"
                        disabled={inputs.length === 1}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Input IDs (e.g., input1, input2) are used as parameter names
                  in the execute function
                </p>
              </div>

              {/* Timeout Configuration */}
              <div className="space-y-2">
                <Label htmlFor="timeout">Execution Timeout</Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="timeout"
                    type="number"
                    value={timeout}
                    onChange={(e) => setTimeout(Number(e.target.value))}
                    min={100}
                    max={10000}
                    className="w-32"
                  />
                  <span className="text-sm text-muted-foreground">
                    milliseconds
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Maximum time allowed for function execution (100-10000ms)
                </p>
              </div>
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

      {/* Expanded Code Editor Dialog */}
      <Dialog open={showExpandedEditor} onOpenChange={setShowExpandedEditor}>
        <DialogContent className="max-w-6xl w-[90vw] h-[90vh] max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>
              Code Editor - {node.data?.label || 'Function'}
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 border rounded-md overflow-hidden">
              <Editor
                height="100%"
                defaultLanguage="javascript"
                value={expandedCode}
                onChange={(value) => setExpandedCode(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: true },
                  fontSize: 16,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 2,
                  insertSpaces: true,
                  wordWrap: 'on',
                  folding: true,
                  lineDecorationsWidth: 10,
                  lineNumbersMinChars: 4,
                  glyphMargin: true,
                  contextmenu: true,
                  selectOnLineNumbers: true,
                  roundedSelection: false,
                  readOnly: false,
                  cursorStyle: 'line',
                  automaticLayout: true,
                }}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleExpandedEditorCancel}>
              Cancel
            </Button>
            <Button onClick={handleExpandedEditorSave}>Apply Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
