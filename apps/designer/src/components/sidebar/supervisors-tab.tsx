'use client'

import { useState } from 'react'
import {
  Plus,
  Settings,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Supervisor {
  id: string
  name: string
  ipAddress?: string
  status: 'active' | 'inactive' | 'error'
  controllerCount: number
  description?: string
}

export function SupervisorsTab() {
  const [supervisors, setSupervisors] = useState<Supervisor[]>([
    {
      id: 'default-supervisor',
      name: 'Default Supervisor',
      status: 'active',
      controllerCount: 0,
      description: 'Local supervisor instance',
    },
  ])
  const [isAddingSupervisor, setIsAddingSupervisor] = useState(false)
  const [newSupervisor, setNewSupervisor] = useState({
    name: '',
    ipAddress: '',
    description: '',
  })

  const handleAddSupervisor = () => {
    if (!newSupervisor.name.trim()) return

    const supervisor: Supervisor = {
      id: `supervisor-${Date.now()}`,
      name: newSupervisor.name,
      ipAddress: newSupervisor.ipAddress || undefined,
      description: newSupervisor.description || undefined,
      status: 'inactive',
      controllerCount: 0,
    }

    setSupervisors((prev) => [...prev, supervisor])
    setNewSupervisor({ name: '', ipAddress: '', description: '' })
    setIsAddingSupervisor(false)
  }

  const handleRemoveSupervisor = (supervisorId: string) => {
    // Don't allow removing the default supervisor
    if (supervisorId === 'default-supervisor') return
    setSupervisors((prev) => prev.filter((s) => s.id !== supervisorId))
  }

  const getStatusIcon = (status: Supervisor['status']) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: Supervisor['status']) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">Supervisors</h3>
          <button
            onClick={() => setIsAddingSupervisor(true)}
            className="p-1 rounded-md hover:bg-accent transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* Add Supervisor Form */}
        {isAddingSupervisor && (
          <div className="mt-3 p-3 border rounded-lg bg-card space-y-2">
            <input
              type="text"
              placeholder="Supervisor name"
              value={newSupervisor.name}
              onChange={(e) =>
                setNewSupervisor((prev) => ({ ...prev, name: e.target.value }))
              }
              className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <input
              type="text"
              placeholder="IP Address (optional)"
              value={newSupervisor.ipAddress}
              onChange={(e) =>
                setNewSupervisor((prev) => ({
                  ...prev,
                  ipAddress: e.target.value,
                }))
              }
              className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newSupervisor.description}
              onChange={(e) =>
                setNewSupervisor((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              className="w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <div className="flex gap-1">
              <button
                onClick={handleAddSupervisor}
                disabled={!newSupervisor.name.trim()}
                className="flex-1 px-2 py-1 text-xs bg-primary text-primary-foreground rounded disabled:bg-muted disabled:text-muted-foreground transition-colors"
              >
                Add
              </button>
              <button
                onClick={() => {
                  setIsAddingSupervisor(false)
                  setNewSupervisor({ name: '', ipAddress: '', description: '' })
                }}
                className="flex-1 px-2 py-1 text-xs border rounded hover:bg-accent transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Supervisors List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {supervisors.map((supervisor) => (
          <div
            key={supervisor.id}
            className="p-3 border rounded-lg bg-card hover:bg-accent/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {getStatusIcon(supervisor.status)}
                <div>
                  <div className="text-sm font-medium">{supervisor.name}</div>
                  {supervisor.ipAddress && (
                    <div className="text-xs text-muted-foreground">
                      {supervisor.ipAddress}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  className="p-1 rounded-md hover:bg-accent transition-colors"
                  title="Settings"
                >
                  <Settings className="w-3 h-3" />
                </button>
                {supervisor.id !== 'default-supervisor' && (
                  <button
                    onClick={() => handleRemoveSupervisor(supervisor.id)}
                    className="p-1 rounded-md hover:bg-destructive/20 hover:text-destructive transition-colors"
                    title="Remove"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            {supervisor.description && (
              <div className="text-xs text-muted-foreground mb-2">
                {supervisor.description}
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="text-xs text-muted-foreground">
                {supervisor.controllerCount} controller
                {supervisor.controllerCount !== 1 ? 's' : ''}
              </div>

              <span
                className={cn(
                  'px-2 py-1 text-xs rounded-full border',
                  getStatusColor(supervisor.status)
                )}
              >
                {supervisor.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t bg-muted/30">
        <div className="text-xs text-muted-foreground">
          Active supervisors manage IoT controllers and execute visual
          programming flows.
        </div>
      </div>
    </div>
  )
}
