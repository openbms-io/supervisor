import { MultistateValueNode } from './multistate-value-node'
import { serializeNodeData, deserializeNodeData } from '@/lib/node-serializer'
import factory from './factory'
import { NodeType } from '@/types/infrastructure'
import { BacnetConfig } from '@/types/infrastructure'

jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
}))

jest.mock('@/types/infrastructure', () => ({
  ...jest.requireActual('@/types/infrastructure'),
  generateInstanceId: jest.fn(
    () => 'test-generated-id-' + Math.random().toString(36).substr(2, 9)
  ),
}))

describe('MultistateValueNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'MSV_001',
    objectType: 'multistate-value',
    objectId: 789,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'System Status',
    discoveredProperties: {
      presentValue: 2,
      stateText: ['Normal', 'Warning', 'Alarm'],
      numberOfStates: 3,
      description: 'Overall system status indicator',
    },
    position: { x: 200, y: 300 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new MultistateValueNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('MSV_001')
      expect(node.objectType).toBe('multistate-value')
      expect(node.type).toBe('multistate-value')
      expect(node.objectId).toBe(789)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('System Status')
      expect(node.label).toBe('System Status')
      expect(node.discoveredProperties).toEqual({
        presentValue: 2,
        stateText: [null, 'Normal', 'Warning', 'Alarm'],
        numberOfStates: 3,
        description: 'Overall system status indicator',
      })
      expect(node.position).toEqual({ x: 200, y: 300 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'MSV_002',
        name: 'Priority Override',
      }
      const node = new MultistateValueNode(config, 'custom-multistate-value-id')

      expect(node.id).toBe('custom-multistate-value-id')
      expect(node.pointId).toBe('MSV_002')
      expect(node.name).toBe('Priority Override')
      expect(node.label).toBe('Priority Override')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'MSV_003',
        objectType: 'multistate-value',
        objectId: 456,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Schedule Mode',
        discoveredProperties: {
          presentValue: 0,
          stateText: ['Occupied', 'Unoccupied', 'Bypass'],
          numberOfStates: 3,
        },
      }
      const node = new MultistateValueNode(config)

      expect(node.objectId).toBe(456)
      expect(node.discoveredProperties.presentValue).toBe(0)
      expect(node.discoveredProperties.numberOfStates).toBe(3)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new MultistateValueNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'multistate-value',
        category: 'bacnet',
        label: 'System Status',
        metadata: {
          pointId: 'MSV_001',
          objectType: 'multistate-value',
          objectId: 789,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'System Status',
          discoveredProperties: {
            presentValue: 2,
            stateText: [null, 'Normal', 'Warning', 'Alarm'],
            numberOfStates: 3,
            description: 'Overall system status indicator',
          },
          position: { x: 200, y: 300 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new MultistateValueNode(
        mockBacnetConfig,
        'multistate-value-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.MULTISTATE_VALUE,
        serializedData: {
          id: 'multistate-value-node',
          type: 'multistate-value',
          category: 'bacnet',
          label: 'System Status',
          metadata: {
            pointId: 'MSV_001',
            objectType: 'multistate-value',
            objectId: 789,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'System Status',
            discoveredProperties: {
              presentValue: 2,
              stateText: [null, 'Normal', 'Warning', 'Alarm'],
              numberOfStates: 3,
              description: 'Overall system status indicator',
            },
            position: { x: 200, y: 300 },
          },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with BacnetConfig', () => {
      const node = factory.createDataNodeFromBacnetConfig({
        config: mockBacnetConfig,
      }) as MultistateValueNode

      expect(node.pointId).toBe('MSV_001')
      expect(node.objectType).toBe('multistate-value')
      expect(node.name).toBe('System Status')
      expect(node.label).toBe('System Status')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'MSV_004',
        objectType: 'multistate-value',
        objectId: 321,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Operating Mode',
        discoveredProperties: {
          presentValue: 1,
          stateText: ['Auto', 'Manual', 'Emergency'],
          numberOfStates: 3,
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as MultistateValueNode

      expect(node.pointId).toBe('MSV_004')
      expect(node.name).toBe('Operating Mode')
      expect(node.objectId).toBe(321)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-multistate-value',
        type: 'multistate-value',
        category: 'bacnet',
        label: 'Restored Multistate Value',
        metadata: {
          pointId: 'MSV_999',
          objectType: 'multistate-value',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Multistate Value',
          discoveredProperties: {
            presentValue: 1,
            stateText: [null, 'State1', 'State2'],
            numberOfStates: 2,
          },
          position: { x: 500, y: 600 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.MULTISTATE_VALUE) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'multistate-value'
            objectId: number
            supervisorId: string
            controllerId: string
            name: string
            discoveredProperties: Record<string, unknown>
            position?: { x: number; y: number }
          }
          return factory.createDataNodeFromBacnetConfig({
            config: {
              pointId: metadata.pointId,
              objectType: metadata.objectType,
              objectId: metadata.objectId,
              supervisorId: metadata.supervisorId,
              controllerId: metadata.controllerId,
              name: metadata.name,
              discoveredProperties: metadata.discoveredProperties,
              position: metadata.position,
            },
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: NodeType.MULTISTATE_VALUE,
        serializedData,
        nodeFactory,
      }) as MultistateValueNode

      expect(result.pointId).toBe('MSV_999')
      expect(result.name).toBe('Restored Multistate Value')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(1)
      expect(result.position).toEqual({ x: 500, y: 600 })
      expect(result.type).toBe('multistate-value')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new MultistateValueNode(
        mockBacnetConfig,
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.MULTISTATE_VALUE) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'multistate-value'
            objectId: number
            supervisorId: string
            controllerId: string
            name: string
            discoveredProperties: Record<string, unknown>
            position?: { x: number; y: number }
          }
          return factory.createDataNodeFromBacnetConfig({
            config: {
              pointId: metadata.pointId,
              objectType: metadata.objectType,
              objectId: metadata.objectId,
              supervisorId: metadata.supervisorId,
              controllerId: metadata.controllerId,
              name: metadata.name,
              discoveredProperties: metadata.discoveredProperties,
              position: metadata.position,
            },
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as MultistateValueNode

      expect(restored.pointId).toBe(original.pointId)
      expect(restored.objectType).toBe(original.objectType)
      expect(restored.type).toBe(original.type)
      expect(restored.objectId).toBe(original.objectId)
      expect(restored.supervisorId).toBe(original.supervisorId)
      expect(restored.controllerId).toBe(original.controllerId)
      expect(restored.name).toBe(original.name)
      expect(restored.label).toBe(original.label)
      expect(restored.discoveredProperties.presentValue).toBe(
        original.discoveredProperties.presentValue
      )
      expect(restored.discoveredProperties.numberOfStates).toBe(
        original.discoveredProperties.numberOfStates
      )
      expect(restored.discoveredProperties.description).toBe(
        original.discoveredProperties.description
      )
      expect(restored.position).toEqual(original.position)
      expect(restored.category).toBe(original.category)
    })
  })
})
