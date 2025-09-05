import { Project, CreateProject } from '@/app/api/projects/schemas'

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface ProjectsContainerProps {}

export interface ProjectsListProps {
  projects: Project[]
  onEdit: ({ id }: { id: string }) => void
  onDelete: ({ id }: { id: string }) => void
  onView: ({ id }: { id: string }) => void
  isLoading: boolean
  error: Error | null
}

export interface ProjectCardProps {
  project: Project
  onEdit: ({ id }: { id: string }) => void
  onDelete: ({ id }: { id: string }) => void
  onView: ({ id }: { id: string }) => void
}

export interface CreateProjectDialogProps {
  isOpen: boolean
  onSubmit: ({ project }: { project: CreateProject }) => Promise<void>
  onClose: () => void
  isPending: boolean
}

export interface SearchAndFilterProps {
  onSearch: ({ query }: { query: string }) => void
  onSort: ({ sort, order }: { sort: ProjectSort; order: ProjectOrder }) => void
  searchQuery: string
  currentSort: ProjectSort
  currentOrder: ProjectOrder
}

export interface DeleteConfirmDialogProps {
  isOpen: boolean
  projectName: string
  onConfirm: () => void
  onCancel: () => void
  isPending: boolean
}

export interface EditProjectDialogProps {
  isOpen: boolean
  project: Project | null
  onSubmit: ({
    id,
    project,
  }: {
    id: string
    project: Partial<CreateProject>
  }) => Promise<void>
  onClose: () => void
  isPending: boolean
}

export interface SearchState {
  query: string
  sort: ProjectSort
  order: ProjectOrder
}

export type ProjectSort = 'name' | 'created_at' | 'updated_at'
export type ProjectOrder = 'asc' | 'desc'

export interface ProjectQueryState {
  search?: string
  sort: ProjectSort
  order: ProjectOrder
  page: number
  limit: number
}
