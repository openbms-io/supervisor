'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { CreateProject } from '@/app/api/projects/schemas'
import {
  useProjects,
  useCreateProject,
  useDeleteProject,
  useUpdateProject,
} from '@/hooks/use-projects'
import { ProjectsList } from './ProjectsList'
import { CreateProjectDialog } from './CreateProjectDialog'
import { EditProjectDialog } from './EditProjectDialog'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'
import { SearchAndFilter } from './SearchAndFilter'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import {
  ProjectsContainerProps,
  SearchState,
  ProjectSort,
  ProjectOrder,
  ProjectQueryState,
} from './types'

export function ProjectsContainer({}: ProjectsContainerProps): React.JSX.Element {
  const router = useRouter()
  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    sort: 'updated_at',
    order: 'desc',
  })

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState<boolean>(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState<boolean>(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState<boolean>(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null
  )

  // Query parameters for API call
  const queryParams: ProjectQueryState = {
    search: searchState.query || undefined,
    sort: searchState.sort,
    order: searchState.order,
    page: 1,
    limit: 50,
  }

  const { data, isLoading, error } = useProjects(queryParams)
  const createProjectMutation = useCreateProject()
  const updateProjectMutation = useUpdateProject()
  const deleteProjectMutation = useDeleteProject()

  const selectedProject =
    data?.projects.find((p) => p.id === selectedProjectId) || null

  const handleSearch = ({ query }: { query: string }): void => {
    setSearchState((prev) => ({ ...prev, query }))
  }

  const handleSort = ({
    sort,
    order,
  }: {
    sort: ProjectSort
    order: ProjectOrder
  }): void => {
    setSearchState((prev) => ({ ...prev, sort, order }))
  }

  const handleCreateProject = async ({
    project,
  }: {
    project: CreateProject
  }): Promise<void> => {
    try {
      await createProjectMutation.mutateAsync(project)
      setIsCreateDialogOpen(false)
    } catch (error) {
      console.error('Failed to create project:', error)
      throw error
    }
  }

  const handleEditProject = async ({
    id,
    project,
  }: {
    id: string
    project: Partial<CreateProject>
  }): Promise<void> => {
    try {
      await updateProjectMutation.mutateAsync({ params: { id, data: project } })
      setIsEditDialogOpen(false)
      setSelectedProjectId(null)
    } catch (error) {
      console.error('Failed to update project:', error)
      throw error
    }
  }

  const handleDeleteProject = async (): Promise<void> => {
    if (!selectedProjectId) return

    try {
      await deleteProjectMutation.mutateAsync(selectedProjectId)
      setIsDeleteDialogOpen(false)
      setSelectedProjectId(null)
    } catch (error) {
      console.error('Failed to delete project:', error)
    }
  }

  const handleView = ({ id }: { id: string }): void => {
    router.push(`/projects/${id}`)
  }

  const handleEdit = ({ id }: { id: string }): void => {
    setSelectedProjectId(id)
    setIsEditDialogOpen(true)
  }

  const handleDelete = ({ id }: { id: string }): void => {
    setSelectedProjectId(id)
    setIsDeleteDialogOpen(true)
  }

  const handleCloseCreateDialog = (): void => {
    setIsCreateDialogOpen(false)
  }

  const handleCloseEditDialog = (): void => {
    setIsEditDialogOpen(false)
    setSelectedProjectId(null)
  }

  const handleCancelDelete = (): void => {
    setIsDeleteDialogOpen(false)
    setSelectedProjectId(null)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Projects</h1>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </div>

      <div className="mb-6">
        <SearchAndFilter
          onSearch={handleSearch}
          onSort={handleSort}
          searchQuery={searchState.query}
          currentSort={searchState.sort}
          currentOrder={searchState.order}
        />
      </div>

      <ProjectsList
        projects={data?.projects || []}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onView={handleView}
        isLoading={isLoading}
        error={error}
      />

      <CreateProjectDialog
        isOpen={isCreateDialogOpen}
        onSubmit={handleCreateProject}
        onClose={handleCloseCreateDialog}
        isPending={createProjectMutation.isPending}
      />

      <EditProjectDialog
        isOpen={isEditDialogOpen}
        project={selectedProject}
        onSubmit={handleEditProject}
        onClose={handleCloseEditDialog}
        isPending={updateProjectMutation.isPending}
      />

      <DeleteConfirmDialog
        isOpen={isDeleteDialogOpen}
        projectName={selectedProject?.name || ''}
        onConfirm={handleDeleteProject}
        onCancel={handleCancelDelete}
        isPending={deleteProjectMutation.isPending}
      />
    </div>
  )
}
