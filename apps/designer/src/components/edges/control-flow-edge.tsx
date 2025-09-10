'use client'

import React from 'react'
import { EdgeProps, getSmoothStepPath, BaseEdge } from '@xyflow/react'
import { EdgeData } from '@/types/infrastructure'

/**
 * Custom edge component for control flow visualization
 * Shows active/inactive state with different styling
 */
export default function ControlFlowEdge(props: EdgeProps) {
  const {
    sourceX = 0,
    sourceY = 0,
    targetX = 0,
    targetY = 0,
    sourcePosition,
    targetPosition,
    data,
    markerEnd,
    style,
  } = props
  // Use smooth step path for better visual appearance
  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  // Edge is active unless explicitly set to false
  const isActive = data?.isActive !== false

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
