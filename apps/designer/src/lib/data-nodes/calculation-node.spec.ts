import { CalculationNode, CalculationOperation } from './calculation-node'
import { serializeNodeData, deserializeNodeData } from '@/lib/node-serializer'
import factory from './factory'
import { NodeType } from '@/types/infrastructure'

// Mock UUID to avoid Jest issues
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
}))

jest.mock('@/types/infrastructure', () => ({
  ...jest.requireActual('@/types/infrastructure'),
  generateInstanceId: jest.fn(
    () => 'test-generated-id-' + Math.random().toString(36).substr(2, 9)
  ),
}))

describe('CalculationNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const node = new CalculationNode('Test Calc', 'add', 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe(NodeType.CALCULATION)
      expect(node.label).toBe('Test Calc')
      expect(node.metadata.operation).toBe('add')
    })

    it('should create node with provided id', () => {
      const customId = 'test-calc-123'
      const node = new CalculationNode('Test Calc', 'multiply', customId)

      expect(node.id).toBe(customId)
      expect(node.type).toBe(NodeType.CALCULATION)
      expect(node.label).toBe('Test Calc')
      expect(node.metadata.operation).toBe('multiply')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new CalculationNode(
        'My Calculator',
        'subtract',
        'test-id-456'
      )

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: NodeType.CALCULATION,
        category: 'logic',
        label: 'My Calculator',
        metadata: { operation: 'subtract' },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new CalculationNode('Divider', 'divide', 'div-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.CALCULATION,
        serializedData: {
          id: 'div-node',
          type: NodeType.CALCULATION,
          category: 'logic',
          label: 'Divider',
          metadata: { operation: 'divide' },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const node = factory.createCalculationNode({
        label: 'Factory Calc',
        operation: 'average',
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Calc')
      expect((node as CalculationNode).metadata.operation).toBe('average')
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createCalculationNode({
        label: 'Factory Calc 2',
        operation: 'add',
        id: 'factory-calc-id',
      })

      expect(node.label).toBe('Factory Calc 2')
      expect((node as CalculationNode).metadata.operation).toBe('add')
      expect(node.id).toBe('factory-calc-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-calc',
        type: NodeType.CALCULATION,
        category: 'logic',
        label: 'Restored Calculator',
        metadata: { operation: 'multiply' },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.CALCULATION) {
          const metadata = data.metadata as { operation: CalculationOperation }
          return factory.createCalculationNode({
            label: data.label as string,
            operation: metadata?.operation,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: NodeType.CALCULATION,
        serializedData,
        nodeFactory,
      }) as CalculationNode

      expect(result.id).toBe('deserialized-calc')
      expect(result.label).toBe('Restored Calculator')
      expect(result.metadata.operation).toBe('multiply')
      expect(result.type).toBe(NodeType.CALCULATION)
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      // Create original node
      const original = new CalculationNode(
        'Round Trip',
        'average',
        'round-trip-id'
      )

      // Serialize
      const serialized = serializeNodeData(original)

      // Create nodeFactory
      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.CALCULATION) {
          const metadata = data.metadata as { operation: CalculationOperation }
          return factory.createCalculationNode({
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
      }) as CalculationNode

      // Verify all properties match
      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.metadata.operation).toBe(original.metadata.operation)
      expect(restored.category).toBe(original.category)
    })
  })
})
