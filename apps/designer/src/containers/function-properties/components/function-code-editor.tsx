import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Maximize2 } from 'lucide-react'
import Editor from '@monaco-editor/react'
import {
  getInlineEditorOptions,
  EDITOR_THEME,
  EDITOR_LANGUAGE,
} from '../utils/monaco-config'

interface FunctionCodeEditorProps {
  code: string
  onCodeChange: (code: string) => void
  onExpandEditor: () => void
}

export const FunctionCodeEditor = ({
  code,
  onCodeChange,
  onExpandEditor,
}: FunctionCodeEditorProps) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor="code">JavaScript Code</Label>
        <Button
          size="sm"
          variant="outline"
          onClick={onExpandEditor}
          className="h-8"
        >
          <Maximize2 className="w-3 h-3 mr-1" />
          Expand
        </Button>
      </div>
      <div className="border rounded-md overflow-hidden">
        <Editor
          height="250px"
          defaultLanguage={EDITOR_LANGUAGE}
          value={code}
          onChange={(value) => onCodeChange(value || '')}
          theme={EDITOR_THEME}
          options={getInlineEditorOptions()}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        Define a function named &apos;execute&apos; that takes the inputs as
        parameters and returns a value
      </p>
    </div>
  )
}
