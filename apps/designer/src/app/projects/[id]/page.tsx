import { MainLayout } from '@/components/layout/main-layout'
import { InfrastructureSidebar } from '@/components/sidebar/infrastructure-sidebar'
import { FlowCanvas } from '@/components/canvas/flow-canvas'
import { WorkflowLoader } from '@/components/canvas/workflow-loader'

interface ProjectPageProps {
  params: Promise<{ id: string }>
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { id } = await params

  return (
    <MainLayout
      projectName={`Project ${id}`}
      sidebar={<InfrastructureSidebar />}
    >
      <WorkflowLoader projectId={id} />
      <FlowCanvas projectId={id} />
    </MainLayout>
  )
}
