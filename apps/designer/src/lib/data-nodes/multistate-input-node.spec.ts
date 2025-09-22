import { MultistateInputNode } from './multistate-input-node'
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

describe('MultistateInputNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'MSI_001',
    objectType: 'multistate-input',
    objectId: 123,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'VAV Damper Position',
    discoveredProperties: {
      presentValue: 2,
      stateText: ['Closed', 'Open', 'Modulating'],
      numberOfStates: 3,
      description: 'VAV damper position feedback',
    },
    position: { x: 100, y: 200 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new MultistateInputNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('MSI_001')
      expect(node.objectType).toBe('multistate-input')
      expect(node.type).toBe('multistate-input')
      expect(node.objectId).toBe(123)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('VAV Damper Position')
      expect(node.label).toBe('VAV Damper Position')
      expect(node.discoveredProperties).toEqual({
        presentValue: 2,
        stateText: [null, 'Closed', 'Open', 'Modulating'],
        numberOfStates: 3,
        description: 'VAV damper position feedback',
      })
      expect(node.position).toEqual({ x: 100, y: 200 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'MSI_002',
        name: 'Fan Speed Status',
      }
      const node = new MultistateInputNode(config, 'custom-multistate-input-id')

      expect(node.id).toBe('custom-multistate-input-id')
      expect(node.pointId).toBe('MSI_002')
      expect(node.name).toBe('Fan Speed Status')
      expect(node.label).toBe('Fan Speed Status')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'MSI_003',
        objectType: 'multistate-input',
        objectId: 456,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'System Mode',
        discoveredProperties: {
          presentValue: 1,
          stateText: ['Off', 'Heat', 'Cool', 'Auto'],
          numberOfStates: 4,
        },
      }
      const node = new MultistateInputNode(config)

      expect(node.objectId).toBe(456)
      expect(node.discoveredProperties.presentValue).toBe(1)
      expect(node.discoveredProperties.numberOfStates).toBe(4)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new MultistateInputNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'multistate-input',
        category: 'bacnet',
        label: 'VAV Damper Position',
        metadata: {
          pointId: 'MSI_001',
          objectType: 'multistate-input',
          objectId: 123,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'VAV Damper Position',
          discoveredProperties: {
            presentValue: 2,
            stateText: [null, 'Closed', 'Open', 'Modulating'],
            numberOfStates: 3,
            description: 'VAV damper position feedback',
          },
          position: { x: 100, y: 200 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new MultistateInputNode(
        mockBacnetConfig,
        'multistate-input-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.MULTISTATE_INPUT,
        serializedData: {
          id: 'multistate-input-node',
          type: 'multistate-input',
          category: 'bacnet',
          label: 'VAV Damper Position',
          metadata: {
            pointId: 'MSI_001',
            objectType: 'multistate-input',
            objectId: 123,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'VAV Damper Position',
            discoveredProperties: {
              presentValue: 2,
              stateText: [null, 'Closed', 'Open', 'Modulating'],
              numberOfStates: 3,
              description: 'VAV damper position feedback',
            },
            position: { x: 100, y: 200 },
          },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with BacnetConfig', () => {
      const node = factory.createDataNodeFromBacnetConfig({
        config: mockBacnetConfig,
      }) as MultistateInputNode

      expect(node.pointId).toBe('MSI_001')
      expect(node.objectType).toBe('multistate-input')
      expect(node.name).toBe('VAV Damper Position')
      expect(node.label).toBe('VAV Damper Position')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'MSI_004',
        objectType: 'multistate-input',
        objectId: 789,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Alarm Status',
        discoveredProperties: {
          presentValue: 0,
          stateText: ['Normal', 'Warning', 'Critical'],
          numberOfStates: 3,
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as MultistateInputNode

      expect(node.pointId).toBe('MSI_004')
      expect(node.name).toBe('Alarm Status')
      expect(node.objectId).toBe(789)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-multistate-input',
        type: 'multistate-input',
        category: 'bacnet',
        label: 'Restored Multistate Input',
        metadata: {
          pointId: 'MSI_999',
          objectType: 'multistate-input',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Multistate Input',
          discoveredProperties: {
            presentValue: 1,
            stateText: ['State1', 'State2'],
            numberOfStates: 2,
          },
          position: { x: 300, y: 400 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.MULTISTATE_INPUT) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'multistate-input'
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
        nodeType: NodeType.MULTISTATE_INPUT,
        serializedData,
        nodeFactory,
      }) as MultistateInputNode

      expect(result.pointId).toBe('MSI_999')
      expect(result.name).toBe('Restored Multistate Input')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(1)
      expect(result.position).toEqual({ x: 300, y: 400 })
      expect(result.type).toBe('multistate-input')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new MultistateInputNode(
        mockBacnetConfig,
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.MULTISTATE_INPUT) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'multistate-input'
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
      }) as MultistateInputNode

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
