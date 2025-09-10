'use client'

import { Handle, HandleProps, useNodeConnections } from '@xyflow/react'

interface CustomHandleProps extends HandleProps {
  connectionCount?: number
}

export const CustomHandle = ({
  connectionCount,
  ...props
}: CustomHandleProps) => {
  // Get all connections for this node
  const connections = useNodeConnections()

  // Filter connections for this specific handle
  const handleConnections = connections.filter((connection) => {
    // For target handles, check if this handle is the target
    if (props.type === 'target') {
      return connection.targetHandle === props.id
    }
    // For source handles, check if this handle is the source
    return connection.sourceHandle === props.id
  })

  const isConnectable =
    connectionCount === undefined || handleConnections.length < connectionCount

  return (
    <Handle
      {...props}
      isConnectable={isConnectable}
      className={`${props.className} ${!isConnectable ? 'opacity-50' : ''}`}
    />
  )
}
