import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import Editor from '@monaco-editor/react'
import {
  getExpandedEditorOptions,
  EDITOR_THEME,
  EDITOR_LANGUAGE,
} from '../utils/monaco-config'

interface FunctionExpandedEditorProps {
  isOpen: boolean
  nodeLabel: string
  code: string
  onCodeChange: (code: string) => void
  onSave: () => void
  onCancel: () => void
}

export const FunctionExpandedEditor = ({
  isOpen,
  nodeLabel,
  code,
  onCodeChange,
  onSave,
  onCancel,
}: FunctionExpandedEditorProps) => {
  return (
    <Dialog open={isOpen} onOpenChange={onCancel}>
      <DialogContent className="max-w-6xl w-[90vw] h-[90vh] max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Code Editor - {nodeLabel}</DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 border rounded-md overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage={EDITOR_LANGUAGE}
              value={code}
              onChange={(value) => onCodeChange(value || '')}
              theme={EDITOR_THEME}
              options={getExpandedEditorOptions()}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={onSave}>Apply Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
