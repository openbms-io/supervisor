'use client'

import React, { useState, useEffect } from 'react'
import { CreateProject } from '@/app/api/projects/schemas'
import { EditProjectDialogProps } from './types'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function EditProjectDialog({
  isOpen,
  project,
  onSubmit,
  onClose,
  isPending,
}: EditProjectDialogProps): React.JSX.Element {
  const [formData, setFormData] = useState<Partial<CreateProject>>({
    name: '',
    description: '',
  })
  const [errors, setErrors] = useState<{ name?: string; description?: string }>(
    {}
  )

  // Update form data when project changes
  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name,
        description: project.description || '',
      })
      setErrors({})
    }
  }, [project])

  const validateForm = ({
    data,
  }: {
    data: Partial<CreateProject>
  }): boolean => {
    const newErrors: { name?: string; description?: string } = {}

    if (data.name !== undefined) {
      if (!data.name.trim()) {
        newErrors.name = 'Project name is required'
      } else if (data.name.length < 2) {
        newErrors.name = 'Project name must be at least 2 characters'
      } else if (data.name.length > 100) {
        newErrors.name = 'Project name must be less than 100 characters'
      }
    }

    if (data.description !== undefined && data.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()

    if (!project || !validateForm({ data: formData })) {
      return
    }

    try {
      await onSubmit({ id: project.id, project: formData })
      setErrors({})
    } catch (error) {
      console.error('Failed to update project:', error)
    }
  }

  const handleInputChange = ({
    field,
    value,
  }: {
    field: keyof CreateProject
    value: string
  }): void => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field as keyof typeof errors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }))
    }
  }

  const handleClose = (): void => {
    setErrors({})
    onClose()
  }

  if (!project) {
    return <></>
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <label htmlFor="edit-name" className="text-sm font-medium">
                Project Name *
              </label>
              <Input
                id="edit-name"
                type="text"
                value={formData.name || ''}
                onChange={(e) =>
                  handleInputChange({ field: 'name', value: e.target.value })
                }
                placeholder="Enter project name..."
                className={errors.name ? 'border-destructive' : ''}
                disabled={isPending}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="edit-description" className="text-sm font-medium">
                Description
              </label>
              <Input
                id="edit-description"
                type="text"
                value={formData.description || ''}
                onChange={(e) =>
                  handleInputChange({
                    field: 'description',
                    value: e.target.value,
                  })
                }
                placeholder="Enter project description..."
                className={errors.description ? 'border-destructive' : ''}
                disabled={isPending}
              />
              {errors.description && (
                <p className="text-sm text-destructive">{errors.description}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Updating...' : 'Update Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
