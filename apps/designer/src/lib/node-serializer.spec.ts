import { serializeNodeData, deserializeNodeData } from './node-serializer'
import { CalculationNode } from './data-nodes/calculation-node'
import { createNodeFactory } from './workflow/serializer'
import type { DataNode } from '@/types/infrastructure'

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

describe('NodeSerializer', () => {
  describe('serializeNodeData', () => {
    it('should use type property from toSerializable, not constructor.name', () => {
      const node = new CalculationNode('Test Calc', 'add', 'test-id-123')

      const serialized = serializeNodeData(node)

      // Should use the type property from toSerializable()
      expect(serialized.nodeType).toBe('calculation')
      // Should NOT use the constructor name
      expect(serialized.nodeType).not.toBe('CalculationNode')
      expect(serialized.serializedData.type).toBe('calculation')
    })

    it('should handle minified constructor names correctly', () => {
      // Create a mock node with minified constructor name (simulating production build)
      const mockNode = {
        constructor: { name: 'aH' }, // Simulated minified name
        toSerializable: jest.fn(() => ({
          type: 'calculation',
          id: 'test-id',
          category: 'logic',
          label: 'Test Minified',
          metadata: { operation: 'add' },
        })),
      }

      const serialized = serializeNodeData(mockNode)

      // Should use 'calculation' from type property, not 'aH' from constructor.name
      expect(serialized.nodeType).toBe('calculation')
      expect(serialized.nodeType).not.toBe('aH')
      expect(mockNode.toSerializable).toHaveBeenCalled()
    })

    it('should serialize CalculationNode correctly', () => {
      const node = new CalculationNode('Add Operation', 'add', 'calc-node-1')

      const serialized = serializeNodeData(node)

      expect(serialized).toEqual({
        nodeType: 'calculation',
        serializedData: {
          id: 'calc-node-1',
          type: 'calculation',
          category: 'logic',
          label: 'Add Operation',
          metadata: { operation: 'add' },
        },
      })
    })

    it('should throw error for non-serializable objects', () => {
      const nonSerializableNode = {
        someProperty: 'value',
        // Missing toSerializable method
      }

      expect(() => serializeNodeData(nonSerializableNode)).toThrow(
        'Cannot serialize node: Node must implement SerializableNode interface'
      )
    })

    it('should throw error for null/undefined objects', () => {
      expect(() => serializeNodeData(null)).toThrow(
        'Cannot serialize node: Node must implement SerializableNode interface'
      )

      expect(() => serializeNodeData(undefined)).toThrow(
        'Cannot serialize node: Node must implement SerializableNode interface'
      )
    })
  })

  describe('deserializeNodeData', () => {
    it('should deserialize using the nodeFactory', () => {
      const mockFactory = jest
        .fn()
        .mockReturnValue({ id: 'test', label: 'Deserialized' })
      const nodeType = 'calculation'
      const serializedData = {
        id: 'test-id',
        type: 'calculation',
        label: 'Test Node',
      }

      const result = deserializeNodeData({
        nodeType,
        serializedData,
        nodeFactory: mockFactory,
      })

      expect(mockFactory).toHaveBeenCalledWith(nodeType, serializedData)
      expect(result).toEqual({ id: 'test', label: 'Deserialized' })
    })

    it('should handle calculation node deserialization', () => {
      const nodeFactory = createNodeFactory()
      const serializedData = {
        id: 'calc-123',
        type: 'calculation',
        category: 'logic',
        label: 'Test Calculation',
        metadata: { operation: 'multiply' },
      }

      const result = deserializeNodeData({
        nodeType: 'calculation',
        serializedData,
        nodeFactory,
      })

      expect(result).toBeDefined()
      expect((result as DataNode).id).toBe('calc-123')
      expect((result as DataNode).label).toBe('Test Calculation')
      expect((result as DataNode).type).toBe('calculation')
    })
  })

  describe('Integration: Minification resilience', () => {
    it('should work even when constructor.name is minified', () => {
      // Create a node that simulates having a minified constructor name
      const node = new CalculationNode(
        'Resilient Node',
        'subtract',
        'resilient-123'
      )

      // Mock the constructor name to simulate minification
      Object.defineProperty(node.constructor, 'name', {
        value: 'XyZ', // Minified name
        configurable: true,
      })

      const serialized = serializeNodeData(node)

      // Should still use the correct type from toSerializable()
      expect(serialized.nodeType).toBe('calculation')
      expect(serialized.nodeType).not.toBe('XyZ')
      expect(serialized.serializedData.type).toBe('calculation')
    })

    it('should roundtrip serialize/deserialize correctly', () => {
      const originalNode = new CalculationNode(
        'Roundtrip Test',
        'divide',
        'roundtrip-456'
      )
      const nodeFactory = createNodeFactory()

      // Serialize
      const serialized = serializeNodeData(originalNode)

      // Deserialize
      const deserialized = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      })

      // Verify the roundtrip worked
      expect((deserialized as CalculationNode).id).toBe('roundtrip-456')
      expect((deserialized as CalculationNode).label).toBe('Roundtrip Test')
      expect((deserialized as CalculationNode).type).toBe('calculation')
      expect((deserialized as CalculationNode).metadata.operation).toBe(
        'divide'
      )
    })

    it('should prevent the original "aH" nodeType issue', () => {
      // This is the exact scenario that was causing the error
      const mockMinifiedNode = {
        constructor: { name: 'aH' }, // The problematic minified name
        toSerializable: () => ({
          type: 'calculation',
          id: 'problematic-node',
          category: 'logic',
          label: 'Previously Broken',
          metadata: { operation: 'add' },
        }),
      }

      const serialized = serializeNodeData(mockMinifiedNode)
      const nodeFactory = createNodeFactory()

      // This should NOT throw "Unknown node type: aH"
      expect(() =>
        deserializeNodeData({
          nodeType: serialized.nodeType,
          serializedData: serialized.serializedData,
          nodeFactory,
        })
      ).not.toThrow()

      // And it should work correctly
      const result = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      })

      expect(result).toBeDefined()
      expect((result as DataNode).type).toBe('calculation')
    })
  })
})
