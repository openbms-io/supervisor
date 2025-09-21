'use client'

import React, { useState } from 'react'
import { CreateProject } from '@/app/api/projects/schemas'
import { CreateProjectDialogProps } from './types'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function CreateProjectDialog({
  isOpen,
  onSubmit,
  onClose,
  isPending,
}: CreateProjectDialogProps): React.JSX.Element {
  const [formData, setFormData] = useState<CreateProject>({
    name: '',
    description: '',
  })
  const [errors, setErrors] = useState<{ name?: string; description?: string }>(
    {}
  )

  const validateForm = ({ data }: { data: CreateProject }): boolean => {
    const newErrors: { name?: string; description?: string } = {}

    if (!data.name.trim()) {
      newErrors.name = 'Project name is required'
    } else if (data.name.length < 2) {
      newErrors.name = 'Project name must be at least 2 characters'
    } else if (data.name.length > 100) {
      newErrors.name = 'Project name must be less than 100 characters'
    }

    if (data.description && data.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()

    if (!validateForm({ data: formData })) {
      return
    }

    try {
      await onSubmit({ project: formData })
      // Reset form on successful submission
      setFormData({ name: '', description: '' })
      setErrors({})
    } catch (error) {
      console.error('Failed to create project:', error)
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
    setFormData({ name: '', description: '' })
    setErrors({})
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Project Name *
              </label>
              <Input
                id="name"
                type="text"
                value={formData.name}
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
              <label htmlFor="description" className="text-sm font-medium">
                Description
              </label>
              <Input
                id="description"
                type="text"
                value={formData.description}
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
              {isPending ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
