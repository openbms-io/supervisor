import { NextRequest, NextResponse } from 'next/server'
import { deploymentConfigRepository } from '@/lib/db/deployment-config'
import {
  CreateDeploymentConfigSchema,
  UpdateDeploymentConfigSchema,
  DeploymentConfigResponseSchema,
} from '@/app/api/projects/[id]/deployment-config/schemas'
import { ZodError } from 'zod'

interface RouteParams {
  params: Promise<{ id: string }>
}

export async function GET(
  request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse> {
  try {
    const { id: projectId } = await params
    const config = await deploymentConfigRepository.getByProjectId(projectId)

    const response = DeploymentConfigResponseSchema.parse({
      success: true,
      config,
    })

    return NextResponse.json(response)
  } catch (error) {
    console.error('Failed to get deployment config:', error)

    const response = DeploymentConfigResponseSchema.parse({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    })

    return NextResponse.json(response, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse> {
  try {
    const { id: projectId } = await params
    const body = await request.json()

    const existingConfig =
      await deploymentConfigRepository.getByProjectId(projectId)

    const validatedData = existingConfig
      ? UpdateDeploymentConfigSchema.parse(body)
      : CreateDeploymentConfigSchema.parse(body)

    const config = await deploymentConfigRepository.createOrUpdate(
      projectId,
      validatedData
    )

    const response = DeploymentConfigResponseSchema.parse({
      success: true,
      config,
    })

    return NextResponse.json(response)
  } catch (error) {
    console.error('Failed to update deployment config:', error)

    if (error instanceof ZodError) {
      const response = DeploymentConfigResponseSchema.parse({
        success: false,
        error: `Validation error: ${error.errors
          .map((e) => e.message)
          .join(', ')}`,
      })

      return NextResponse.json(response, { status: 400 })
    }

    const response = DeploymentConfigResponseSchema.parse({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error',
    })

    return NextResponse.json(response, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse> {
  try {
    const { id: projectId } = await params
    await deploymentConfigRepository.delete(projectId)

    const response = DeploymentConfigResponseSchema.parse({
      success: true,
    })

    return NextResponse.json(response)
  } catch (error) {
    console.error('Failed to delete deployment config:', error)

    const response = DeploymentConfigResponseSchema.parse({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error',
    })

    return NextResponse.json(response, { status: 500 })
  }
}
