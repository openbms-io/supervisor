'use client'

import { Handle, HandleProps, useHandleConnections } from '@xyflow/react'

interface CustomHandleProps extends HandleProps {
  connectionCount?: number
}

export const CustomHandle = ({
  connectionCount,
  ...props
}: CustomHandleProps) => {
  const connections = useHandleConnections({
    type: props.type,
    id: props.id,
  })

  const isConnectable =
    connectionCount === undefined || connections.length < connectionCount

  return (
    <Handle
      {...props}
      isConnectable={isConnectable}
      className={`${props.className} ${!isConnectable ? 'opacity-50' : ''}`}
    />
  )
}
