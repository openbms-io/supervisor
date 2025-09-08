'use client'

// External libraries
import { useCallback, useRef, DragEvent } from 'react'
import {
  ReactFlow,
  // MiniMap,  // Temporarily disabled
  Controls,
  Background,
  Connection,
  BackgroundVariant,
  ReactFlowInstance,
  Node,
  Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

// Internal absolute imports
import { useFlowStore } from '@/store/use-flow-store'
import { nodeTypes } from '@/components/nodes'

export function FlowCanvas() {
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null)

  // Get handlers
  const onNodesChange = useFlowStore((state) => state.onNodesChange)
  const onEdgesChange = useFlowStore((state) => state.onEdgesChange)

  // Get nodes/edges from state (not from dataGraph)
  const nodes = useFlowStore((state) => state.nodes)
  const edges = useFlowStore((state) => state.edges)

  const connectNodes = useFlowStore((state) => state.connectNodes)
  const addNodeFromInfrastructure = useFlowStore(
    (state) => state.addNodeFromInfrastructure
  )
  const addLogicNode = useFlowStore((state) => state.addLogicNode)
  const addCommandNode = useFlowStore((state) => state.addCommandNode)
  const removeNode = useFlowStore((state) => state.removeNode)

  const onConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target) {
        connectNodes(params.source, params.target)
      }
    },
    [connectNodes]
  )

  const onNodeDelete = useCallback(
    (nodes: Node[]) => {
      nodes.forEach((node) => removeNode(node.id))
    },
    [removeNode]
  )

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }, [])

  const onDrop = useCallback(
    async (event: DragEvent) => {
      event.preventDefault()

      if (!reactFlowInstance.current) {
        console.warn('React Flow instance not ready')
        return
      }

      const data = event.dataTransfer.getData('application/json')
      if (!data) {
        console.warn('No drag data found')
        return
      }

      try {
        const draggedData = JSON.parse(data)
        // Get the position where the node was dropped
        const position = reactFlowInstance.current.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        })

        if (
          draggedData.type === 'bacnet-point' &&
          draggedData.draggedFrom === 'controllers-tree'
        ) {
          // Add BACnet node from infrastructure
          await addNodeFromInfrastructure(draggedData, position)
        } else if (
          draggedData.type === 'logic-node' &&
          draggedData.draggedFrom === 'logic-section'
        ) {
          // Add logic node
          await addLogicNode(
            draggedData.nodeType,
            draggedData.label,
            position,
            draggedData.metadata
          )
        } else if (
          draggedData.type === 'command-node' &&
          draggedData.draggedFrom === 'command-section'
        ) {
          // Add command node
          await addCommandNode(
            draggedData.nodeType,
            draggedData.label,
            position,
            draggedData.metadata
          )
        } else {
          console.warn('Unknown drag type:', draggedData.type)
        }
      } catch (error) {
        console.error('Failed to handle drop:', error)
      }
    },
    [addNodeFromInfrastructure, addLogicNode, addCommandNode]
  )

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstance.current = instance
  }, [])

  return (
    <div className="w-full h-full bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodesDelete={onNodeDelete}
        onConnect={onConnect}
        onInit={onInit}
        onDragOver={onDragOver}
        onDrop={onDrop}
        fitView
        deleteKeyCode={['Delete', 'Backspace']}
        className="bg-background"
      >
        <Controls
          className="bg-card border border-border"
          showZoom={true}
          showFitView={true}
          showInteractive={false}
        />
        {/* MiniMap disabled temporarily - causing node rendering issues
        <MiniMap
          className="bg-card border border-border"
          maskColor="rgba(0, 0, 0, 0.1)"
          pannable
          zoomable
        />
        */}
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="hsl(var(--muted-foreground))"
          style={{
            opacity: 0.5,
          }}
        />
      </ReactFlow>
    </div>
  )
}
