'use client'

import React from 'react'
import { EdgeProps, getSmoothStepPath, BaseEdge } from '@xyflow/react'
import { useFlowStore } from '@/store/use-flow-store'

/**
 * Custom edge component for control flow visualization
 * Shows active/inactive state with different styling
 */
export default function ControlFlowEdge(props: EdgeProps) {
  const {
    id,
    sourceX = 0,
    sourceY = 0,
    targetX = 0,
    targetY = 0,
    sourcePosition,
    targetPosition,
    markerEnd,
    style,
  } = props

  const isActive = useFlowStore(
    (state) => state.edges.find((e) => e.id === id)?.data?.isActive !== false
  )

  // Use smooth step path for better visual appearance
  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  // Handle optional style prop
  const edgeStyle = style || {}

  // Merge custom styles with default styles
  const customStyle = {
    ...edgeStyle,
    stroke: isActive ? '#0ea5e9' : '#94a3b8', // sky-500 for active, slate-400 for inactive
    strokeWidth: isActive ? 2 : 1,
    strokeDasharray: isActive ? undefined : '5 5', // undefined for solid line
    opacity: isActive ? 1 : 0.5,
    // Removed transition - not supported properly on SVG paths
  }

  return <BaseEdge path={edgePath} markerEnd={markerEnd} style={customStyle} />
}
