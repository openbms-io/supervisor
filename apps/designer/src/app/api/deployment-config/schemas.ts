import { z } from 'zod'

export const DeploymentConfigSchema = z.object({
  id: z.string().uuid(),
  organization_id: z
    .string()
    .min(1, 'Organization ID is required')
    .regex(/^org_/, 'Organization ID must start with "org_"'),
  site_id: z
    .string()
    .min(1, 'Site ID is required')
    .max(255, 'Site ID too long'),
  device_id: z
    .string()
    .min(1, 'Device ID is required')
    .max(255, 'Device ID too long'),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export const UpdateDeploymentConfigSchema = z
  .object({
    organization_id: z
      .string()
      .min(1, 'Organization ID is required')
      .regex(/^org_/, 'Organization ID must start with "org_"')
      .optional(),
    site_id: z
      .string()
      .min(1, 'Site ID is required')
      .max(255, 'Site ID too long')
      .optional(),
    device_id: z
      .string()
      .min(1, 'Device ID is required')
      .max(255, 'Device ID too long')
      .optional(),
  })
  .refine(
    (data) =>
      data.organization_id !== undefined ||
      data.site_id !== undefined ||
      data.device_id !== undefined,
    {
      message: 'At least one field must be provided',
    }
  )

export type DeploymentConfig = z.infer<typeof DeploymentConfigSchema>
export type UpdateDeploymentConfig = z.infer<
  typeof UpdateDeploymentConfigSchema
>

export const DeploymentConfigResponseSchema = z.object({
  success: z.boolean(),
  config: DeploymentConfigSchema.optional(),
  error: z.string().optional(),
})

export type DeploymentConfigResponse = z.infer<
  typeof DeploymentConfigResponseSchema
>
