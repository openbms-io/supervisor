'use client'

import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { useFlowStore } from '@/store/use-flow-store'
import { Save, Loader2, Check } from 'lucide-react'

interface SaveProjectButtonProps {
  projectId: string
}

export function SaveProjectButton({ projectId }: SaveProjectButtonProps) {
  const saveProject = useFlowStore((state) => state.saveProject)
  const saveStatus = useFlowStore((state) => state.saveStatus)
  const [showSaved, setShowSaved] = useState(false)

  const handleSave = useCallback(async () => {
    try {
      await saveProject({ projectId })
    } catch (err) {
      console.error('Save failed:', err)
    }
  }, [projectId, saveProject])

  // Cmd+S / Ctrl+S keyboard shortcut
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const isMac =
        typeof navigator !== 'undefined' &&
        navigator.platform.toUpperCase().includes('MAC')
      const mod = isMac ? e.metaKey : e.ctrlKey
      if (mod && (e.key === 's' || e.key === 'S')) {
        e.preventDefault()
        void handleSave()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [handleSave])

  // Show "Saved" briefly then revert label
  useEffect(() => {
    if (saveStatus === 'saved') {
      setShowSaved(true)
      const t = setTimeout(() => setShowSaved(false), 3000)
      return () => clearTimeout(t)
    }
  }, [saveStatus])

  return (
    <Button
      onClick={handleSave}
      size="sm"
      className="flex items-center gap-2"
      variant="secondary"
      disabled={saveStatus === 'saving'}
    >
      {saveStatus === 'saving' ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Saving...
        </>
      ) : saveStatus === 'saved' && showSaved ? (
        <>
          <Check className="h-4 w-4" />
          Saved
        </>
      ) : (
        <>
          <Save className="h-4 w-4" />
          Save
        </>
      )}
    </Button>
  )
}
