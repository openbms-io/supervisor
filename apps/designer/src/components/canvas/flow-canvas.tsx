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
  Panel,
  EdgeTypes,
} from '@xyflow/react'
import { PlayIcon } from 'lucide-react'
import '@xyflow/react/dist/style.css'

// Internal absolute imports
import { useFlowStore } from '@/store/use-flow-store'
import { nodeTypes } from '@/components/nodes'
import ControlFlowEdge from '@/components/edges/control-flow-edge'
import { Button } from '@/components/ui/button'
import { NotificationHandler } from './notification-handler'
import { EDGE_TYPES } from '@/types/edge-types'
import BidirectionalFlowEdge from '../edges/bidirectional-flow-edge'

// Edge types for visualization
// Only register custom edge types, React Flow handles built-in types automatically
const edgeTypes = {
  [EDGE_TYPES.CONTROL_FLOW]: ControlFlowEdge, // Register our custom edge type
  [EDGE_TYPES.BIDIRECTIONAL_FLOW]: BidirectionalFlowEdge, // Register our custom edge type
} satisfies EdgeTypes

import { SaveProjectButton } from './save-project-button'

export function FlowCanvas({ projectId }: { projectId: string }) {
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
  const addControlFlowNode = useFlowStore((state) => state.addControlFlowNode)
  const removeNode = useFlowStore((state) => state.removeNode)
  const executeWithMessages = useFlowStore((state) => state.executeWithMessages)

  const onConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target) {
        connectNodes(
          params.source,
          params.target,
          params.sourceHandle,
          params.targetHandle
        )
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
        } else if (
          draggedData.type === 'control-flow-node' &&
          draggedData.draggedFrom === 'control-flow-section'
        ) {
          // Add control flow node
          await addControlFlowNode(
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
    [
      addNodeFromInfrastructure,
      addLogicNode,
      addCommandNode,
      addControlFlowNode,
    ]
  )

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstance.current = instance
  }, [])

  return (
    <div className="w-full h-full bg-background">
      {/* Notification handler component */}
      <NotificationHandler />

      <ReactFlow
        nodes={nodes as Node[]}
        edges={edges as Edge[]}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
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
        <Panel position="top-center" className="m-2">
          <div className="flex gap-2">
            <Button
              onClick={executeWithMessages}
              size="sm"
              className="flex items-center gap-2"
              variant="default"
            >
              <PlayIcon className="h-4 w-4" />
              Run
            </Button>

            <SaveProjectButton projectId={projectId} />
          </div>
        </Panel>
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
