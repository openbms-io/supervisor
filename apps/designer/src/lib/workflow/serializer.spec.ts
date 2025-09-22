import { Node, Edge } from '@xyflow/react'
import { ConstantNode } from '@/lib/data-nodes/constant-node'
import { SCHEMA_VERSION } from 'bms-schemas'

// Mock UUID to avoid Jest issues
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
}))
import {
  serializeWorkflow,
  deserializeWorkflow,
  createWorkflowConfig,
  validateWorkflowConfig,
  serializeFromReactFlowObject,
  prepareForReactFlow,
  createNodeFactory,
  type WorkflowMetadata,
  type VersionedWorkflowConfig,
} from './serializer'

describe('WorkflowSerializer', () => {
  // Create real ConstantNode instances with specific IDs for predictable testing
  const constantNode1 = new ConstantNode(
    'Constant Value',
    42,
    'number',
    'test-constant-node-1'
  )
  const constantNode2 = new ConstantNode(
    'Boolean Constant',
    true,
    'boolean',
    'test-constant-node-2'
  )

  const mockNodes: Node<Record<string, unknown>>[] = [
    {
      id: constantNode1.id,
      type: 'logic.constant',
      position: { x: 100, y: 100 },
      data: constantNode1 as unknown as Record<string, unknown>,
    },
    {
      id: constantNode2.id,
      type: 'logic.constant',
      position: { x: 300, y: 150 },
      data: constantNode2 as unknown as Record<string, unknown>,
    },
  ]

  const mockEdges: Edge[] = [
    {
      id: 'edge-1',
      source: constantNode1.id,
      target: constantNode2.id,
      sourceHandle: 'output',
      targetHandle: 'input-1',
    },
  ]

  const nodeFactory = createNodeFactory()

  const mockMetadata: WorkflowMetadata = {
    lastModified: '2025-09-19T10:30:00Z',
    createdBy: 'test-user',
    description: 'Test workflow',
  }

  describe('createWorkflowConfig', () => {
    it('should create workflow config with correct structure', () => {
      const config = createWorkflowConfig({
        nodes: mockNodes,
        edges: mockEdges,
        metadata: mockMetadata,
      })

      expect(config.metadata).toEqual(mockMetadata)
      expect(config.edges).toEqual(mockEdges)
      expect(config.nodes).toHaveLength(2)

      // Check the first serialized node
      expect(config.nodes[0]).toEqual({
        id: 'test-constant-node-1',
        type: 'logic.constant',
        position: { x: 100, y: 100 },
        data: {
          nodeType: 'constant',
          serializedData: {
            id: 'test-constant-node-1',
            type: 'constant',
            category: 'logic',
            label: 'Constant Value',
            metadata: {
              value: 42,
              valueType: 'number',
            },
          },
        },
      })
    })

    it('should create workflow config with minimal metadata', () => {
      const minimalMetadata: WorkflowMetadata = {
        lastModified: '2025-09-19T10:30:00Z',
      }

      const config = createWorkflowConfig({
        nodes: mockNodes,
        edges: mockEdges,
        metadata: minimalMetadata,
      })

      expect(config.metadata).toEqual(minimalMetadata)
      expect(config.nodes).toHaveLength(2)
      expect(config.edges).toEqual(mockEdges)
    })
  })

  describe('serializeWorkflow', () => {
    it('should serialize React Flow state to versioned workflow config', () => {
      const reactFlowObject = {
        nodes: mockNodes,
        edges: mockEdges,
        viewport: { x: 0, y: 0, zoom: 1 },
      }

      const serialized = serializeWorkflow({
        reactFlowObject,
        metadata: mockMetadata,
      })

      expect(serialized).toHaveProperty('schema_info')
      expect(serialized.schema_info).toMatchObject({
        version: '1.0.0',
        compatibility: '>=1.0.0',
        schema_name: 'WorkflowConfig',
      })
      expect(serialized.schema_info.generated_at).toBeDefined()
      expect(serialized.schema_info.generated_at).toBeDefined()
      expect(serialized.data.nodes).toHaveLength(2)
      expect(serialized.data.edges).toEqual(mockEdges)
      expect(serialized.data.metadata).toEqual(mockMetadata)
    })

    it('should handle empty nodes and edges', () => {
      const emptyReactFlowObject = {
        nodes: [],
        edges: [],
        viewport: { x: 0, y: 0, zoom: 1 },
      }

      const serialized = serializeWorkflow({
        reactFlowObject: emptyReactFlowObject,
        metadata: mockMetadata,
      })

      expect(serialized.data.nodes).toEqual([])
      expect(serialized.data.edges).toEqual([])
      expect(serialized.data.metadata).toEqual(mockMetadata)
    })
  })

  describe('deserializeWorkflow', () => {
    it('should deserialize versioned workflow config to React Flow state', () => {
      // First create a serialized config from our real nodes
      const workflowConfig = createWorkflowConfig({
        nodes: mockNodes,
        edges: mockEdges,
        metadata: mockMetadata,
      })

      const versionedConfig: VersionedWorkflowConfig = {
        schema_info: {
          version: SCHEMA_VERSION,
          compatibility: '>=1.0.0',
          schema_name: 'WorkflowConfig',
          generated_at: '2025-09-19T10:30:00Z',
        },
        data: workflowConfig,
      }

      const reactFlowState = deserializeWorkflow({
        versionedConfig,
        nodeFactory,
      })

      expect(reactFlowState.nodes).toHaveLength(2)
      expect(reactFlowState.edges).toEqual(mockEdges)
      expect(reactFlowState.metadata).toEqual(mockMetadata)

      // Check that nodes were properly deserialized
      const deserializedNode = reactFlowState.nodes[0]
      expect(deserializedNode.id).toBe('test-constant-node-1')
      expect(deserializedNode.type).toBe('logic.constant')
      expect(deserializedNode.data).toBeInstanceOf(ConstantNode)
    })

    it('should handle empty versioned config', () => {
      const emptyVersionedConfig: VersionedWorkflowConfig = {
        schema_info: {
          version: SCHEMA_VERSION,
          compatibility: '>=1.0.0',
          schema_name: 'WorkflowConfig',
        },
        data: {
          metadata: { lastModified: '2025-09-19T10:30:00Z' },
          nodes: [],
          edges: [],
        },
      }

      const reactFlowState = deserializeWorkflow({
        versionedConfig: emptyVersionedConfig,
        nodeFactory,
      })

      expect(reactFlowState.nodes).toEqual([])
      expect(reactFlowState.edges).toEqual([])
      expect(reactFlowState.metadata.lastModified).toBe('2025-09-19T10:30:00Z')
    })
  })

  describe('validateWorkflowConfig', () => {
    it('should validate correct workflow config', () => {
      const validConfig = createWorkflowConfig({
        nodes: mockNodes,
        edges: mockEdges,
        metadata: mockMetadata,
      })

      const result = validateWorkflowConfig({ config: validConfig })

      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual([])
    })

    it('should reject config with invalid metadata', () => {
      const invalidConfig = {
        metadata: {
          lastModified: 'invalid-date',
        },
        nodes: mockNodes,
        edges: mockEdges,
      }

      const result = validateWorkflowConfig({ config: invalidConfig })

      expect(result.isValid).toBe(false)
      expect(result.errors.length).toBeGreaterThan(0)
    })

    it('should reject config without required fields', () => {
      const invalidConfig = {
        nodes: mockNodes,
        // Missing metadata and edges
      }

      const result = validateWorkflowConfig({ config: invalidConfig })

      expect(result.isValid).toBe(false)
      expect(result.errors.length).toBeGreaterThan(0)
    })
  })

  describe('React Flow integration', () => {
    it('should serialize from React Flow toObject() result', () => {
      const toObjectResult = {
        nodes: mockNodes,
        edges: mockEdges,
        viewport: { x: 0, y: 0, zoom: 1 },
      }

      const serialized = serializeFromReactFlowObject({
        toObjectResult,
        metadata: mockMetadata,
      })

      expect(serialized.schema_info).toMatchObject({
        version: '1.0.0',
        compatibility: '>=1.0.0',
        schema_name: 'WorkflowConfig',
      })
      expect(serialized.schema_info.generated_at).toBeDefined()
      expect(serialized.data.nodes).toHaveLength(2)
      expect(serialized.data.edges).toEqual(mockEdges)
      expect(serialized.data.metadata).toEqual(mockMetadata)
    })

    it('should prepare data for React Flow setNodes/setEdges', () => {
      // Create a proper serialized config first
      const workflowConfig = createWorkflowConfig({
        nodes: mockNodes,
        edges: mockEdges,
        metadata: mockMetadata,
      })

      const versionedConfig: VersionedWorkflowConfig = {
        schema_info: {
          version: SCHEMA_VERSION,
          compatibility: '>=1.0.0',
          schema_name: 'WorkflowConfig',
        },
        data: workflowConfig,
      }

      const reactFlowData = prepareForReactFlow({
        versionedConfig,
        nodeFactory,
      })

      expect(reactFlowData.nodes).toHaveLength(2)
      expect(reactFlowData.edges).toEqual(mockEdges)
      expect(reactFlowData.metadata).toEqual(mockMetadata)
      expect(reactFlowData.nodes[0].data).toBeInstanceOf(ConstantNode)
    })
  })

  describe('Schema versioning', () => {
    it('should include correct version information', () => {
      const reactFlowObject = {
        nodes: mockNodes,
        edges: mockEdges,
        viewport: { x: 0, y: 0, zoom: 1 },
      }

      const serialized = serializeWorkflow({
        reactFlowObject,
        metadata: mockMetadata,
      })

      expect(serialized.schema_info).toMatchObject({
        version: '1.0.0',
        compatibility: '>=1.0.0',
        schema_name: 'WorkflowConfig',
      })
      expect(serialized.schema_info.generated_at).toBeDefined()
    })

    it('should handle version compatibility', () => {
      const futureVersionConfig: VersionedWorkflowConfig = {
        schema_info: {
          version: '2.0.0',
          compatibility: '>=2.0.0',
          schema_name: 'WorkflowConfig',
        },
        data: {
          metadata: mockMetadata,
          nodes: mockNodes,
          edges: mockEdges,
        },
      }

      expect(() => {
        validateWorkflowConfig({ config: futureVersionConfig.data })
      }).not.toThrow()
    })
  })
})
