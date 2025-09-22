import { TimerNode } from './timer-node'
import { serializeNodeData, deserializeNodeData } from '@/lib/node-serializer'
import factory from './factory'
import { NodeType } from '@/types/infrastructure'

jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
}))

jest.mock('@/types/infrastructure', () => ({
  ...jest.requireActual('@/types/infrastructure'),
  generateInstanceId: jest.fn(
    () => 'test-generated-id-' + Math.random().toString(36).substr(2, 9)
  ),
}))

describe('TimerNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const node = new TimerNode('Test Timer', 5000, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('timer')
      expect(node.label).toBe('Test Timer')
      expect(node.duration).toBe(5000)
      expect(node.metadata.duration).toBe(5000)
      expect(node.category).toBe('control-flow')
      expect(node.isRunning).toBe(false)
      expect(node.tickCount).toBe(0)
    })

    it('should create node with provided id', () => {
      const node = new TimerNode('Test Timer', 2000, 'custom-timer-id')

      expect(node.id).toBe('custom-timer-id')
      expect(node.type).toBe('timer')
      expect(node.label).toBe('Test Timer')
      expect(node.duration).toBe(2000)
    })

    it('should handle different durations', () => {
      const fastNode = new TimerNode('Fast Timer', 100)
      const slowNode = new TimerNode('Slow Timer', 10000)

      expect(fastNode.duration).toBe(100)
      expect(slowNode.duration).toBe(10000)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new TimerNode('My Timer', 3000, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'timer',
        category: 'control-flow',
        label: 'My Timer',
        metadata: { duration: 3000 },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new TimerNode('Pulse Timer', 1500, 'timer-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.TIMER,
        serializedData: {
          id: 'timer-node',
          type: 'timer',
          category: 'control-flow',
          label: 'Pulse Timer',
          metadata: { duration: 1500 },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const node = factory.createTimerNode({
        label: 'Factory Timer',
        duration: 2500,
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Timer')
      expect((node as TimerNode).duration).toBe(2500)
      expect((node as TimerNode).metadata.duration).toBe(2500)
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createTimerNode({
        label: 'Factory Timer 2',
        duration: 500,
        id: 'factory-timer-id',
      })

      expect(node.label).toBe('Factory Timer 2')
      expect((node as TimerNode).duration).toBe(500)
      expect(node.id).toBe('factory-timer-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-timer',
        type: 'timer',
        category: 'control-flow',
        label: 'Restored Timer',
        metadata: { duration: 4000 },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.TIMER) {
          const metadata = data.metadata as { duration: number }
          return factory.createTimerNode({
            label: data.label as string,
            duration: metadata?.duration,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: NodeType.TIMER,
        serializedData,
        nodeFactory,
      }) as TimerNode

      expect(result.id).toBe('deserialized-timer')
      expect(result.label).toBe('Restored Timer')
      expect(result.duration).toBe(4000)
      expect(result.metadata.duration).toBe(4000)
      expect(result.type).toBe('timer')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new TimerNode('Round Trip', 7500, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.TIMER) {
          const metadata = data.metadata as { duration: number }
          return factory.createTimerNode({
            label: data.label as string,
            duration: metadata?.duration,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as TimerNode

      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.duration).toBe(original.duration)
      expect(restored.metadata.duration).toBe(original.metadata.duration)
      expect(restored.category).toBe(original.category)
    })
  })
})
