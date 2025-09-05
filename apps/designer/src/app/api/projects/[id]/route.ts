import { NextRequest, NextResponse } from 'next/server'
import { UpdateProjectSchema } from '../schemas'
import { projectsRepository } from '../../../../lib/db/projects'
import { ZodError } from 'zod'

interface RouteParams {
  params: Promise<{ id: string }>
}

export async function GET(
  request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse> {
  try {
    const { id } = await params

    const project = projectsRepository.findById(id)

    if (!project) {
      return NextResponse.json(
        {
          success: false,
          error: 'Project not found',
        },
        { status: 404 }
      )
    }

    const response = {
      success: true,
      project,
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('Error fetching project:', error)

    return NextResponse.json(
      {
        success: false,
        error: 'Failed to fetch project',
      },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse> {
  try {
    const { id } = await params
    const body = await request.json()

    const data = UpdateProjectSchema.parse(body)

    const project = projectsRepository.update(id, data)

    if (!project) {
      return NextResponse.json(
        {
          success: false,
          error: 'Project not found',
        },
        { status: 404 }
      )
    }

    const response = {
      success: true,
      project,
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('Error updating project:', error)

    if (error instanceof ZodError) {
      return NextResponse.json(
        {
          success: false,
          error: `Invalid project data: ${error.errors
            .map((e) => e.message)
            .join(', ')}`,
        },
        { status: 400 }
      )
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Failed to update project',
      },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: RouteParams
): Promise<NextResponse> {
  try {
    const { id } = await params

    const deleted = projectsRepository.delete(id)

    if (!deleted) {
      return NextResponse.json(
        {
          success: false,
          error: 'Project not found',
        },
        { status: 404 }
      )
    }

    const response = {
      success: true,
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('Error deleting project:', error)

    return NextResponse.json(
      {
        success: false,
        error: 'Failed to delete project',
      },
      { status: 500 }
    )
  }
}
