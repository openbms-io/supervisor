interface ProjectPageProps {
  params: Promise<{ id: string }>
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { id } = await params

  return (
    <div>
      <h1>Project {id}</h1>
      <p>Project editor will be implemented here.</p>
    </div>
  )
}
