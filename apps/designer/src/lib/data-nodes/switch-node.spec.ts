import { SwitchNode } from './switch-node'
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

describe('SwitchNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const node = new SwitchNode(
        'Test Switch',
        'gt',
        50,
        'High',
        'Low',
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('switch')
      expect(node.label).toBe('Test Switch')
      expect(node.condition).toBe('gt')
      expect(node.threshold).toBe(50)
      expect(node.activeLabel).toBe('High')
      expect(node.inactiveLabel).toBe('Low')
      expect(node.category).toBe('control-flow')
    })

    it('should create node with provided id', () => {
      const node = new SwitchNode(
        'Test Switch',
        'lt',
        25,
        undefined,
        undefined,
        'custom-switch-id'
      )

      expect(node.id).toBe('custom-switch-id')
      expect(node.type).toBe('switch')
      expect(node.label).toBe('Test Switch')
      expect(node.condition).toBe('lt')
      expect(node.threshold).toBe(25)
    })

    it('should handle different conditions', () => {
      const gtNode = new SwitchNode('GT Switch', 'gt', 10)
      const lteNode = new SwitchNode('LTE Switch', 'lte', 100)
      const eqNode = new SwitchNode('EQ Switch', 'eq', 0)

      expect(gtNode.condition).toBe('gt')
      expect(lteNode.condition).toBe('lte')
      expect(eqNode.condition).toBe('eq')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new SwitchNode(
        'My Switch',
        'gte',
        75,
        'Active',
        'Inactive',
        'test-id-456'
      )

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'switch',
        category: 'control-flow',
        label: 'My Switch',
        metadata: {
          condition: 'gte',
          threshold: 75,
          activeLabel: 'Active',
          inactiveLabel: 'Inactive',
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new SwitchNode(
        'Boolean Switch',
        'eq',
        1,
        'True',
        'False',
        'switch-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'SwitchNode',
        serializedData: {
          id: 'switch-node',
          type: 'switch',
          category: 'control-flow',
          label: 'Boolean Switch',
          metadata: {
            condition: 'eq',
            threshold: 1,
            activeLabel: 'True',
            inactiveLabel: 'False',
          },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const node = factory.createSwitchNode({
        label: 'Factory Switch',
        condition: 'lt',
        threshold: 30,
        activeLabel: 'Cold',
        inactiveLabel: 'Hot',
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Switch')
      expect((node as SwitchNode).condition).toBe('lt')
      expect((node as SwitchNode).threshold).toBe(30)
      expect((node as SwitchNode).activeLabel).toBe('Cold')
      expect((node as SwitchNode).inactiveLabel).toBe('Hot')
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createSwitchNode({
        label: 'Factory Switch 2',
        condition: 'gte',
        threshold: 85,
        id: 'factory-switch-id',
      })

      expect(node.label).toBe('Factory Switch 2')
      expect((node as SwitchNode).condition).toBe('gte')
      expect((node as SwitchNode).threshold).toBe(85)
      expect(node.id).toBe('factory-switch-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-switch',
        type: 'switch',
        category: 'control-flow',
        label: 'Restored Switch',
        metadata: {
          condition: 'lte',
          threshold: 60,
          activeLabel: 'Low',
          inactiveLabel: 'High',
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'SwitchNode') {
          const metadata = data.metadata as {
            condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
            threshold: number
            activeLabel: string
            inactiveLabel: string
          }
          return factory.createSwitchNode({
            label: data.label as string,
            condition: metadata?.condition,
            threshold: metadata?.threshold,
            activeLabel: metadata?.activeLabel,
            inactiveLabel: metadata?.inactiveLabel,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: 'SwitchNode',
        serializedData,
        nodeFactory,
      }) as SwitchNode

      expect(result.id).toBe('deserialized-switch')
      expect(result.label).toBe('Restored Switch')
      expect(result.condition).toBe('lte')
      expect(result.threshold).toBe(60)
      expect(result.activeLabel).toBe('Low')
      expect(result.inactiveLabel).toBe('High')
      expect(result.type).toBe('switch')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new SwitchNode(
        'Round Trip',
        'gt',
        42,
        'Above',
        'Below',
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'SwitchNode') {
          const metadata = data.metadata as {
            condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
            threshold: number
            activeLabel: string
            inactiveLabel: string
          }
          return factory.createSwitchNode({
            label: data.label as string,
            condition: metadata?.condition,
            threshold: metadata?.threshold,
            activeLabel: metadata?.activeLabel,
            inactiveLabel: metadata?.inactiveLabel,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as SwitchNode

      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.condition).toBe(original.condition)
      expect(restored.threshold).toBe(original.threshold)
      expect(restored.activeLabel).toBe(original.activeLabel)
      expect(restored.inactiveLabel).toBe(original.inactiveLabel)
      expect(restored.category).toBe(original.category)
    })
  })
})
