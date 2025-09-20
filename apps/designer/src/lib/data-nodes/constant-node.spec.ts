import { ConstantNode, ConstantNodeMetadata } from './constant-node'
import { serializeNodeData, deserializeNodeData } from '@/lib/node-serializer'
import factory from './factory'

jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
}))

jest.mock('@/types/infrastructure', () => ({
  ...jest.requireActual('@/types/infrastructure'),
  generateInstanceId: jest.fn(
    () => 'test-generated-id-' + Math.random().toString(36).substr(2, 9)
  ),
}))

describe('ConstantNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const node = new ConstantNode(
        'Test Constant',
        42,
        'number',
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('constant')
      expect(node.label).toBe('Test Constant')
      expect(node.metadata.value).toBe(42)
      expect(node.metadata.valueType).toBe('number')
      expect(node.category).toBe('logic')
    })

    it('should create node with provided id', () => {
      const customId = 'test-constant-123'
      const node = new ConstantNode('Test Constant', 100, 'number', customId)

      expect(node.id).toBe(customId)
      expect(node.type).toBe('constant')
      expect(node.label).toBe('Test Constant')
      expect(node.metadata.value).toBe(100)
    })

    it('should handle different value types', () => {
      const numberNode = new ConstantNode('Number', 42, 'number', 'num-id')
      const boolNode = new ConstantNode('Boolean', true, 'boolean', 'bool-id')
      const stringNode = new ConstantNode('String', 'hello', 'string', 'str-id')

      expect(numberNode.metadata.valueType).toBe('number')
      expect(boolNode.metadata.valueType).toBe('boolean')
      expect(stringNode.metadata.valueType).toBe('string')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new ConstantNode(
        'My Constant',
        3.14,
        'number',
        'test-id-456'
      )

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'constant',
        category: 'logic',
        label: 'My Constant',
        metadata: { value: 3.14, valueType: 'number' },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new ConstantNode(
        'Boolean Constant',
        false,
        'boolean',
        'constant-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'ConstantNode',
        serializedData: {
          id: 'constant-node',
          type: 'constant',
          category: 'logic',
          label: 'Boolean Constant',
          metadata: { value: false, valueType: 'boolean' },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const node = factory.createConstantNode({
        label: 'Factory Constant',
        value: 99,
        valueType: 'number',
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Constant')
      expect((node as ConstantNode).metadata.value).toBe(99)
      expect((node as ConstantNode).metadata.valueType).toBe('number')
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createConstantNode({
        label: 'Factory String',
        value: 'test',
        valueType: 'string',
        id: 'factory-string-id',
      })

      expect(node.label).toBe('Factory String')
      expect((node as ConstantNode).metadata.value).toBe('test')
      expect((node as ConstantNode).metadata.valueType).toBe('string')
      expect(node.id).toBe('factory-string-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-constant',
        type: 'constant',
        category: 'logic',
        label: 'Restored Constant',
        metadata: { value: 777, valueType: 'number' },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'ConstantNode') {
          const metadata = data.metadata as ConstantNodeMetadata
          return factory.createConstantNode({
            label: data.label as string,
            value: metadata?.value,
            valueType: metadata?.valueType,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: 'ConstantNode',
        serializedData,
        nodeFactory,
      }) as ConstantNode

      expect(result.id).toBe('deserialized-constant')
      expect(result.label).toBe('Restored Constant')
      expect(result.metadata.value).toBe(777)
      expect(result.metadata.valueType).toBe('number')
      expect(result.type).toBe('constant')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new ConstantNode(
        'Round Trip',
        55.5,
        'number',
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'ConstantNode') {
          const metadata = data.metadata as ConstantNodeMetadata
          return factory.createConstantNode({
            label: data.label as string,
            value: metadata?.value,
            valueType: metadata?.valueType,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as ConstantNode

      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.metadata.value).toBe(original.metadata.value)
      expect(restored.metadata.valueType).toBe(original.metadata.valueType)
      expect(restored.category).toBe(original.category)
    })
  })
})
