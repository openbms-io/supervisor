'use client'

import { ReactNode, useState } from 'react'
import { cn } from '@/lib/utils'

interface MainLayoutProps {
  children: ReactNode
  sidebar: ReactNode
  projectName?: string
}

export function MainLayout({
  children,
  sidebar,
  projectName,
}: MainLayoutProps) {
  const [sidebarWidth, setSidebarWidth] = useState(300)
  const [isResizing, setIsResizing] = useState(false)

  const handleMouseDown = () => {
    setIsResizing(true)
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isResizing) return

    const newWidth = e.clientX
    if (newWidth >= 250 && newWidth <= 500) {
      setSidebarWidth(newWidth)
    }
  }

  const handleMouseUp = () => {
    setIsResizing(false)
  }

  return (
    <div
      className="h-screen flex flex-col bg-background text-foreground"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Header */}
      <header className="h-12 px-4 border-b flex items-center justify-between bg-card">
        <div className="flex items-center gap-3">
          <h1 className="font-semibold text-lg">
            {projectName || 'BMS Designer'}
          </h1>
        </div>

        <div className="flex items-center gap-2" />
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className="bg-card border-r flex-shrink-0 flex flex-col"
          style={{ width: sidebarWidth }}
        >
          {sidebar}
        </aside>

        {/* Resizer */}
        <div
          className={cn(
            'w-1 hover:w-1.5 bg-border hover:bg-primary transition-all cursor-col-resize relative',
            isResizing && 'bg-primary w-1.5'
          )}
          onMouseDown={handleMouseDown}
        >
          <div className="absolute inset-0 hover:bg-primary/20" />
        </div>

        {/* Main Canvas Area */}
        <main className="flex-1 bg-background overflow-hidden">{children}</main>
      </div>
    </div>
  )
}
