import { z } from 'zod'

const uuidRegex =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const orgIdRegex = /^org_[a-zA-Z0-9_-]+$/
const isoDateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/

export const DeploymentConfigSchema = z.object({
  id: z.string().regex(uuidRegex, 'Must be a valid UUID'),
  project_id: z.string().regex(uuidRegex, 'Must be a valid UUID'),
  organization_id: z
    .string()
    .regex(
      orgIdRegex,
      'Must start with "org_" followed by alphanumeric characters, hyphens, or underscores'
    ),
  site_id: z.string().min(1, 'Site ID is required'),
  iot_device_id: z.string().min(1, 'IoT Device ID is required'),
  created_at: z.string().regex(isoDateRegex, 'Must be a valid ISO datetime'),
  updated_at: z.string().regex(isoDateRegex, 'Must be a valid ISO datetime'),
})

export const CreateDeploymentConfigSchema = z.object({
  organization_id: z
    .string()
    .regex(
      orgIdRegex,
      'Must start with "org_" followed by alphanumeric characters, hyphens, or underscores'
    ),
  site_id: z.string().min(1, 'Site ID is required'),
  iot_device_id: z.string().min(1, 'IoT Device ID is required'),
})

export const UpdateDeploymentConfigSchema = z.object({
  organization_id: z
    .string()
    .regex(
      orgIdRegex,
      'Must start with "org_" followed by alphanumeric characters, hyphens, or underscores'
    )
    .optional(),
  site_id: z.string().min(1, 'Site ID is required').optional(),
  iot_device_id: z.string().min(1, 'IoT Device ID is required').optional(),
})

export const DeploymentConfigResponseSchema = z.union([
  z.object({
    success: z.literal(true),
    config: DeploymentConfigSchema.nullable().optional(),
  }),
  z.object({
    success: z.literal(false),
    error: z.string(),
    config: z.undefined().optional(),
  }),
])

export type DeploymentConfig = z.infer<typeof DeploymentConfigSchema>
export type CreateDeploymentConfig = z.infer<
  typeof CreateDeploymentConfigSchema
>
export type UpdateDeploymentConfig = z.infer<
  typeof UpdateDeploymentConfigSchema
>
export type DeploymentConfigResponse = z.infer<
  typeof DeploymentConfigResponseSchema
>
