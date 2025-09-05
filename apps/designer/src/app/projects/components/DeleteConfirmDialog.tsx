import React from 'react'
import { DeleteConfirmDialogProps } from './types'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertTriangle } from 'lucide-react'

export function DeleteConfirmDialog({
  isOpen,
  projectName,
  onConfirm,
  onCancel,
  isPending,
}: DeleteConfirmDialogProps): React.JSX.Element {
  const handleConfirm = (): void => {
    onConfirm()
  }

  const handleCancel = (): void => {
    onCancel()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-destructive" />
            <DialogTitle>Delete Project</DialogTitle>
          </div>
          <DialogDescription className="pt-2">
            Are you sure you want to delete{' '}
            <span className="font-semibold">&ldquo;{projectName}&rdquo;</span>?{' '}
            This action cannot be undone and will permanently remove the project
            and all its data.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleConfirm}
            disabled={isPending}
          >
            {isPending ? 'Deleting...' : 'Delete Project'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
