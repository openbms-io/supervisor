import type { editor } from 'monaco-editor'

export const getInlineEditorOptions =
  (): editor.IStandaloneEditorConstructionOptions => ({
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
  })

export const getExpandedEditorOptions =
  (): editor.IStandaloneEditorConstructionOptions => ({
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
  })

export const EDITOR_THEME = 'vs-dark'
export const EDITOR_LANGUAGE = 'javascript'
