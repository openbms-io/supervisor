import { z } from 'zod'
import { VersionedWorkflowConfigSchema } from '@/lib/workflow/config-schema'

// Base project schema for database storage
export const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z
    .string()
    .min(1, 'Project name is required')
    .max(255, 'Project name too long'),
  description: z.string().optional(),
  workflow_config: z.string().default('{}'), // JSON string for workflow configuration
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

// Schema for creating a new project
export const CreateProjectSchema = z.object({
  name: z
    .string()
    .min(1, 'Project name is required')
    .max(255, 'Project name too long'),
  description: z.string().optional(),
  workflow_config: VersionedWorkflowConfigSchema.optional(),
})

// Schema for updating a project
export const UpdateProjectSchema = z.object({
  name: z
    .string()
    .min(1, 'Project name is required')
    .max(255, 'Project name too long')
    .optional(),
  description: z.string().optional(),
  workflow_config: VersionedWorkflowConfigSchema.optional(),
})

// Schema for project queries
export const ProjectQuerySchema = z.object({
  page: z
    .string()
    .nullish()
    .transform((val) => (val ? Number(val) : 1))
    .pipe(z.number().min(1)),
  limit: z
    .string()
    .nullish()
    .transform((val) => (val ? Number(val) : 20))
    .pipe(z.number().min(1).max(100)),
  search: z.string().nullish(),
  sort: z
    .enum(['name', 'created_at', 'updated_at'])
    .nullish()
    .default('updated_at'),
  order: z.enum(['asc', 'desc']).nullish().default('desc'),
})

// Type exports
export type Project = z.infer<typeof ProjectSchema>
export type CreateProject = z.infer<typeof CreateProjectSchema>
export type UpdateProject = z.infer<typeof UpdateProjectSchema>
export type ProjectQuery = z.infer<typeof ProjectQuerySchema>

// API response schemas
export const ProjectListResponseSchema = z.object({
  projects: z.array(ProjectSchema),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
  pages: z.number(),
})

export const ProjectResponseSchema = z.object({
  success: z.boolean(),
  project: ProjectSchema.optional(),
  error: z.string().optional(),
})

export const ProjectsResponseSchema = z.object({
  success: z.boolean(),
  data: ProjectListResponseSchema.optional(),
  error: z.string().optional(),
})

export type ProjectListResponse = z.infer<typeof ProjectListResponseSchema>
export type ProjectResponse = z.infer<typeof ProjectResponseSchema>
export type ProjectsResponse = z.infer<typeof ProjectsResponseSchema>
