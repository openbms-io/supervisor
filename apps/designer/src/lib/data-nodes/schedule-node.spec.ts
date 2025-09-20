import { ScheduleNode, DayOfWeek, ScheduleNodeMetadata } from './schedule-node'
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

describe('ScheduleNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const days: DayOfWeek[] = ['Mon', 'Wed', 'Fri']
      const node = new ScheduleNode(
        'Test Schedule',
        '09:00',
        '18:00',
        days,
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('schedule')
      expect(node.label).toBe('Test Schedule')
      expect(node.metadata.startTime).toBe('09:00')
      expect(node.metadata.endTime).toBe('18:00')
      expect(node.metadata.days).toEqual(['Mon', 'Wed', 'Fri'])
      expect(node.category).toBe('control-flow')
      expect(node.isActive).toBe(false)
    })

    it('should create node with provided id', () => {
      const node = new ScheduleNode(
        'Test Schedule',
        '10:00',
        '16:00',
        undefined,
        'custom-schedule-id'
      )

      expect(node.id).toBe('custom-schedule-id')
      expect(node.type).toBe('schedule')
      expect(node.label).toBe('Test Schedule')
      expect(node.metadata.startTime).toBe('10:00')
      expect(node.metadata.endTime).toBe('16:00')
    })

    it('should handle different time ranges and days', () => {
      const weekdayNode = new ScheduleNode('Weekday', '08:30', '17:30', [
        'Mon',
        'Tue',
        'Wed',
        'Thu',
        'Fri',
      ])
      const weekendNode = new ScheduleNode('Weekend', '10:00', '22:00', [
        'Sat',
        'Sun',
      ])

      expect(weekdayNode.metadata.days).toEqual([
        'Mon',
        'Tue',
        'Wed',
        'Thu',
        'Fri',
      ])
      expect(weekendNode.metadata.days).toEqual(['Sat', 'Sun'])
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const days: DayOfWeek[] = ['Mon', 'Tue', 'Wed']
      const node = new ScheduleNode(
        'My Schedule',
        '07:00',
        '19:00',
        days,
        'test-id-456'
      )

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'schedule',
        category: 'control-flow',
        label: 'My Schedule',
        metadata: {
          startTime: '07:00',
          endTime: '19:00',
          days: ['Mon', 'Tue', 'Wed'],
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const days: DayOfWeek[] = ['Sat', 'Sun']
      const node = new ScheduleNode(
        'Weekend Schedule',
        '11:00',
        '23:00',
        days,
        'schedule-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'ScheduleNode',
        serializedData: {
          id: 'schedule-node',
          type: 'schedule',
          category: 'control-flow',
          label: 'Weekend Schedule',
          metadata: {
            startTime: '11:00',
            endTime: '23:00',
            days: ['Sat', 'Sun'],
          },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const days: DayOfWeek[] = ['Thu', 'Fri']
      const node = factory.createScheduleNode({
        label: 'Factory Schedule',
        startTime: '06:00',
        endTime: '14:00',
        days,
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Schedule')
      expect((node as ScheduleNode).metadata.startTime).toBe('06:00')
      expect((node as ScheduleNode).metadata.endTime).toBe('14:00')
      expect((node as ScheduleNode).metadata.days).toEqual(['Thu', 'Fri'])
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createScheduleNode({
        label: 'Factory Schedule 2',
        startTime: '12:00',
        endTime: '20:00',
        id: 'factory-schedule-id',
      })

      expect(node.label).toBe('Factory Schedule 2')
      expect((node as ScheduleNode).metadata.startTime).toBe('12:00')
      expect((node as ScheduleNode).metadata.endTime).toBe('20:00')
      expect(node.id).toBe('factory-schedule-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-schedule',
        type: 'schedule',
        category: 'control-flow',
        label: 'Restored Schedule',
        metadata: {
          startTime: '05:30',
          endTime: '21:30',
          days: ['Mon', 'Fri'],
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'ScheduleNode') {
          const metadata = data.metadata as ScheduleNodeMetadata
          return factory.createScheduleNode({
            label: data.label as string,
            startTime: metadata?.startTime,
            endTime: metadata?.endTime,
            days: metadata?.days,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: 'ScheduleNode',
        serializedData,
        nodeFactory,
      }) as ScheduleNode

      expect(result.id).toBe('deserialized-schedule')
      expect(result.label).toBe('Restored Schedule')
      expect(result.metadata.startTime).toBe('05:30')
      expect(result.metadata.endTime).toBe('21:30')
      expect(result.metadata.days).toEqual(['Mon', 'Fri'])
      expect(result.type).toBe('schedule')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const days: DayOfWeek[] = ['Tue', 'Thu', 'Sat']
      const original = new ScheduleNode(
        'Round Trip',
        '13:15',
        '18:45',
        days,
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'ScheduleNode') {
          const metadata = data.metadata as ScheduleNodeMetadata
          return factory.createScheduleNode({
            label: data.label as string,
            startTime: metadata?.startTime,
            endTime: metadata?.endTime,
            days: metadata?.days,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as ScheduleNode

      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.metadata.startTime).toBe(original.metadata.startTime)
      expect(restored.metadata.endTime).toBe(original.metadata.endTime)
      expect(restored.metadata.days).toEqual(original.metadata.days)
      expect(restored.category).toBe(original.category)
    })
  })
})
