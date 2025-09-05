import { NextRequest, NextResponse } from 'next/server'
import { ProjectQuerySchema, CreateProjectSchema } from './schemas'
import { projectsRepository } from '../../../lib/db/projects'
import { ZodError } from 'zod'

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url)

    const query = ProjectQuerySchema.parse({
      page: searchParams.get('page'),
      limit: searchParams.get('limit'),
      search: searchParams.get('search'),
      sort: searchParams.get('sort'),
      order: searchParams.get('order'),
    })

    const data = projectsRepository.list(query)

    const response = {
      success: true,
      data,
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('Error fetching projects:', error)

    if (error instanceof ZodError) {
      return NextResponse.json(
        {
          success: false,
          error: `Invalid query parameters: ${error.errors
            .map((e) => e.message)
            .join(', ')}`,
        },
        { status: 400 }
      )
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Failed to fetch projects',
      },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json()

    const data = CreateProjectSchema.parse(body)

    const project = projectsRepository.create(data)

    const response = {
      success: true,
      project,
    }

    return NextResponse.json(response, { status: 201 })
  } catch (error) {
    console.error('Error creating project:', error)

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
        error: 'Failed to create project',
      },
      { status: 500 }
    )
  }
}
