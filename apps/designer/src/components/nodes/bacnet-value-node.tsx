'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface BacnetNodeData {
  name: string
  objectType: string
  presentValue: number
  units: string
}

export const BacnetValueNode = memo(({ data }: NodeProps) => {
  const nodeData = data as unknown as BacnetNodeData
  return (
    <Card className="min-w-[180px] border-2">
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">{nodeData.name}</span>
          <Badge variant="outline" className="text-xs">
            {nodeData.objectType}
          </Badge>
        </div>

        <div className="text-xs text-muted-foreground">
          Value: {nodeData.presentValue} {nodeData.units}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-primary border-2 border-background"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-primary border-2 border-background"
      />
    </Card>
  )
})

BacnetValueNode.displayName = 'BacnetValueNode'
