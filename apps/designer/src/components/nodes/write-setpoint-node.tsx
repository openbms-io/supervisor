'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PenTool } from 'lucide-react'
interface WriteSetpointData {
  label: string
  metadata?: {
    propertyName?: string
  }
}

export const WriteSetpointNode = memo(({ data }: NodeProps) => {
  const { label, metadata } = data as unknown as WriteSetpointData

  return (
    <Card className="min-w-[180px] border-2 border-orange-500">
      <div className="p-3">
        <div className="flex items-center gap-2 mb-2">
          <PenTool className="w-4 h-4 text-orange-500" />
          <span className="text-sm font-medium">{label}</span>
        </div>

        <div className="space-y-1">
          <Badge variant="outline" className="text-xs">
            Command
          </Badge>
          {metadata?.propertyName && (
            <div className="text-xs text-muted-foreground">
              Property: {metadata.propertyName}
            </div>
          )}
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-orange-500 border-2 border-background"
      />
    </Card>
  )
})

WriteSetpointNode.displayName = 'WriteSetpointNode'
