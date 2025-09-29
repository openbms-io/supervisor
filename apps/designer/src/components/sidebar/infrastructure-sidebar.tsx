'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ControllersTab } from './controllers-tab'
import { SupervisorsTab } from './supervisors-tab'

type TabType = 'controllers' | 'supervisors'

interface InfrastructureSidebarProps {
  projectId: string
}

export function InfrastructureSidebar({
  projectId,
}: InfrastructureSidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>('controllers')

  return (
    <div className="h-full flex flex-col">
      {/* Tab Navigation */}
      <div className="p-2 border-b">
        <div className="flex bg-muted rounded-lg p-1">
          <button
            className={cn(
              'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all',
              activeTab === 'controllers'
                ? 'bg-background shadow-sm text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
            onClick={() => setActiveTab('controllers')}
          >
            Controllers
          </button>
          <button
            className={cn(
              'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all',
              activeTab === 'supervisors'
                ? 'bg-background shadow-sm text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            )}
            onClick={() => setActiveTab('supervisors')}
          >
            Supervisors
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'controllers' && <ControllersTab />}
        {activeTab === 'supervisors' && (
          <SupervisorsTab projectId={projectId} />
        )}
      </div>
    </div>
  )
}
