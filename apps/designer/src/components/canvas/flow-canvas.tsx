'use client'

// External libraries
import { useCallback, useRef, DragEvent } from 'react'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  Connection,
  BackgroundVariant,
  ReactFlowInstance,
  Node,
  NodeChange,
  Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

// Internal absolute imports
import { useFlowStore } from '@/store/use-flow-store'
import { DraggedPoint } from '@/store/slices/flow-slice'
import { NodeDataRecord } from '@/lib/data-graph/data-graph'

export function FlowCanvas() {
  const reactFlowInstance = useRef<ReactFlowInstance<
    Node<NodeDataRecord>,
    Edge
  > | null>(null)

  // Get nodes and edges - stable references from DataGraph
  const nodes = useFlowStore((state) => state.dataGraph.getReactFlowNodes())
  const edges = useFlowStore((state) => state.dataGraph.getReactFlowEdges())

  const connectNodes = useFlowStore((state) => state.connectNodes)
  const updateNodePosition = useFlowStore((state) => state.updateNodePosition)
  const addNodeFromInfrastructure = useFlowStore(
    (state) => state.addNodeFromInfrastructure
  )
  const removeNode = useFlowStore((state) => state.removeNode)

  const onConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target) {
        connectNodes(params.source, params.target)
      }
    },
    [connectNodes]
  )

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      // Handle position changes
      changes.forEach((change) => {
        if (
          change.type === 'position' &&
          change.position &&
          change.dragging === false
        ) {
          updateNodePosition(change.id, change.position)
        }
      })
    },
    [updateNodePosition]
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

      if (!reactFlowInstance.current) return

      const data = event.dataTransfer.getData('application/json')
      if (!data) return

      try {
        const draggedPoint: DraggedPoint = JSON.parse(data)

        if (
          draggedPoint.type === 'bacnet-point' &&
          draggedPoint.draggedFrom === 'controllers-tree'
        ) {
          // Get the position where the node was dropped
          const position = reactFlowInstance.current.screenToFlowPosition({
            x: event.clientX,
            y: event.clientY,
          })

          // Add node to the flow
          await addNodeFromInfrastructure(draggedPoint, position)
        }
      } catch (error) {
        console.error('Failed to handle drop:', error)
      }
    },
    [addNodeFromInfrastructure]
  )

  const onInit = useCallback(
    (instance: ReactFlowInstance<Node<NodeDataRecord>, Edge>) => {
      reactFlowInstance.current = instance
    },
    []
  )

  return (
    <div className="w-full h-full bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
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
        <MiniMap
          className="bg-card border border-border"
          nodeColor={(node) => {
            switch (node.type) {
              default:
                return '#6366f1'
            }
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
          pannable
          zoomable
        />
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
