import { NextRequest, NextResponse } from 'next/server'
import { deploymentConfigRepository } from '@/lib/db/deployment-config'
import {
  UpdateDeploymentConfigSchema,
  DeploymentConfigResponseSchema,
} from './schemas'
import { ZodError } from 'zod'

export async function GET(): Promise<NextResponse> {
  try {
    const config = await deploymentConfigRepository.getOrCreate()

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

export async function PUT(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json()
    const updateData = UpdateDeploymentConfigSchema.parse(body)

    const config = await deploymentConfigRepository.update(updateData)

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
