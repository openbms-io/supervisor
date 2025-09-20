import { WriteSetpointNode } from './write-setpoint-node'
import { serializeNodeData, deserializeNodeData } from '@/lib/node-serializer'
import factory from './factory'

// Mock UUID to avoid Jest issues
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
}))

// Mock generateInstanceId directly since the UUID mock might not work in infrastructure.ts
jest.mock('@/types/infrastructure', () => ({
  ...jest.requireActual('@/types/infrastructure'),
  generateInstanceId: jest.fn(
    () => 'test-generated-id-' + Math.random().toString(36).substr(2, 9)
  ),
}))

describe('WriteSetpointNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const node = new WriteSetpointNode(
        'Test Setpoint',
        12,
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('write-setpoint')
      expect(node.label).toBe('Test Setpoint')
      expect(node.priority).toBe(12)
      expect(node.category).toBe('command')
    })

    it('should create node with provided id', () => {
      const customId = 'test-setpoint-123'
      const node = new WriteSetpointNode('Test Setpoint', 8, customId)

      expect(node.id).toBe(customId)
      expect(node.type).toBe('write-setpoint')
      expect(node.label).toBe('Test Setpoint')
      expect(node.priority).toBe(8)
    })

    it('should clamp priority to valid range', () => {
      const node1 = new WriteSetpointNode('Low Priority', 0, 'test-id-1')
      const node2 = new WriteSetpointNode('High Priority', 20, 'test-id-2')

      expect(node1.priority).toBe(1) // Clamped to min
      expect(node2.priority).toBe(16) // Clamped to max
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new WriteSetpointNode('My Setpoint', 10, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'write-setpoint',
        category: 'command',
        label: 'My Setpoint',
        metadata: { priority: 10 },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new WriteSetpointNode(
        'Override Setpoint',
        5,
        'setpoint-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'WriteSetpointNode',
        serializedData: {
          id: 'setpoint-node',
          type: 'write-setpoint',
          category: 'command',
          label: 'Override Setpoint',
          metadata: { priority: 5 },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const node = factory.createWriteSetpointNode({
        label: 'Factory Setpoint',
        priority: 14,
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Setpoint')
      expect((node as WriteSetpointNode).priority).toBe(14)
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createWriteSetpointNode({
        label: 'Factory Setpoint 2',
        priority: 3,
        id: 'factory-setpoint-id',
      })

      expect(node.label).toBe('Factory Setpoint 2')
      expect((node as WriteSetpointNode).priority).toBe(3)
      expect(node.id).toBe('factory-setpoint-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-setpoint',
        type: 'write-setpoint',
        category: 'command',
        label: 'Restored Setpoint',
        metadata: { priority: 6 },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'WriteSetpointNode') {
          const metadata = data.metadata as { priority: number }
          return factory.createWriteSetpointNode({
            label: data.label as string,
            priority: metadata?.priority,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: 'WriteSetpointNode',
        serializedData,
        nodeFactory,
      }) as WriteSetpointNode

      expect(result.id).toBe('deserialized-setpoint')
      expect(result.label).toBe('Restored Setpoint')
      expect(result.priority).toBe(6)
      expect(result.type).toBe('write-setpoint')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      // Create original node
      const original = new WriteSetpointNode('Round Trip', 11, 'round-trip-id')

      // Serialize
      const serialized = serializeNodeData(original)

      // Create nodeFactory
      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'WriteSetpointNode') {
          const metadata = data.metadata as { priority: number }
          return factory.createWriteSetpointNode({
            label: data.label as string,
            priority: metadata?.priority,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      // Deserialize
      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as WriteSetpointNode

      // Verify all properties match
      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.priority).toBe(original.priority)
      expect(restored.category).toBe(original.category)
    })
  })
})
