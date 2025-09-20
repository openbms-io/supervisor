import { ComparisonNode, ComparisonOperation } from './comparison-node'
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

describe('ComparisonNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const node = new ComparisonNode(
        'Test Compare',
        'equals',
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('comparison')
      expect(node.label).toBe('Test Compare')
      expect(node.metadata.operation).toBe('equals')
    })

    it('should create node with provided id', () => {
      const customId = 'test-compare-123'
      const node = new ComparisonNode('Test Compare', 'greater', customId)

      expect(node.id).toBe(customId)
      expect(node.type).toBe('comparison')
      expect(node.label).toBe('Test Compare')
      expect(node.metadata.operation).toBe('greater')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new ComparisonNode(
        'My Comparator',
        'less-equal',
        'test-id-456'
      )

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'comparison',
        category: 'logic',
        label: 'My Comparator',
        metadata: { operation: 'less-equal' },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new ComparisonNode(
        'Greater Than',
        'greater-equal',
        'gt-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'ComparisonNode',
        serializedData: {
          id: 'gt-node',
          type: 'comparison',
          category: 'logic',
          label: 'Greater Than',
          metadata: { operation: 'greater-equal' },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const node = factory.createComparisonNode({
        label: 'Factory Compare',
        operation: 'less',
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Compare')
      expect((node as ComparisonNode).metadata.operation).toBe('less')
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createComparisonNode({
        label: 'Factory Compare 2',
        operation: 'equals',
        id: 'factory-compare-id',
      })

      expect(node.label).toBe('Factory Compare 2')
      expect((node as ComparisonNode).metadata.operation).toBe('equals')
      expect(node.id).toBe('factory-compare-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-compare',
        type: 'comparison',
        category: 'logic',
        label: 'Restored Comparator',
        metadata: { operation: 'greater' },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'ComparisonNode') {
          const metadata = data.metadata as { operation: ComparisonOperation }
          return factory.createComparisonNode({
            label: data.label as string,
            operation: metadata?.operation,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: 'ComparisonNode',
        serializedData,
        nodeFactory,
      }) as ComparisonNode

      expect(result.id).toBe('deserialized-compare')
      expect(result.label).toBe('Restored Comparator')
      expect(result.metadata.operation).toBe('greater')
      expect(result.type).toBe('comparison')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      // Create original node
      const original = new ComparisonNode(
        'Round Trip',
        'less-equal',
        'round-trip-id'
      )

      // Serialize
      const serialized = serializeNodeData(original)

      // Create nodeFactory
      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'ComparisonNode') {
          const metadata = data.metadata as { operation: ComparisonOperation }
          return factory.createComparisonNode({
            label: data.label as string,
            operation: metadata?.operation,
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
      }) as ComparisonNode

      // Verify all properties match
      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.metadata.operation).toBe(original.metadata.operation)
      expect(restored.category).toBe(original.category)
    })
  })
})
