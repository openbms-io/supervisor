import { MultistateOutputNode } from './multistate-output-node'
import { serializeNodeData, deserializeNodeData } from '@/lib/node-serializer'
import factory from './factory'
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

describe('MultistateOutputNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'MSO_001',
    objectType: 'multistate-output',
    objectId: 456,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'VAV Box Mode',
    discoveredProperties: {
      presentValue: 1,
      stateText: ['Off', 'Heat', 'Cool'],
      numberOfStates: 3,
      description: 'VAV box operating mode',
    },
    position: { x: 150, y: 250 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new MultistateOutputNode(
        mockBacnetConfig,
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('MSO_001')
      expect(node.objectType).toBe('multistate-output')
      expect(node.type).toBe('multistate-output')
      expect(node.objectId).toBe(456)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('VAV Box Mode')
      expect(node.label).toBe('VAV Box Mode')
      expect(node.discoveredProperties).toEqual({
        presentValue: 1,
        stateText: [null, 'Off', 'Heat', 'Cool'],
        numberOfStates: 3,
        description: 'VAV box operating mode',
      })
      expect(node.position).toEqual({ x: 150, y: 250 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'MSO_002',
        name: 'Fan Speed Control',
      }
      const node = new MultistateOutputNode(
        config,
        'custom-multistate-output-id'
      )

      expect(node.id).toBe('custom-multistate-output-id')
      expect(node.pointId).toBe('MSO_002')
      expect(node.name).toBe('Fan Speed Control')
      expect(node.label).toBe('Fan Speed Control')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'MSO_003',
        objectType: 'multistate-output',
        objectId: 789,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Valve Position',
        discoveredProperties: {
          presentValue: 2,
          stateText: ['Closed', 'Modulating', 'Open'],
          numberOfStates: 3,
        },
      }
      const node = new MultistateOutputNode(config)

      expect(node.objectId).toBe(789)
      expect(node.discoveredProperties.presentValue).toBe(2)
      expect(node.discoveredProperties.numberOfStates).toBe(3)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new MultistateOutputNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'multistate-output',
        category: 'bacnet',
        label: 'VAV Box Mode',
        metadata: {
          pointId: 'MSO_001',
          objectType: 'multistate-output',
          objectId: 456,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'VAV Box Mode',
          discoveredProperties: {
            presentValue: 1,
            stateText: [null, 'Off', 'Heat', 'Cool'],
            numberOfStates: 3,
            description: 'VAV box operating mode',
          },
          position: { x: 150, y: 250 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new MultistateOutputNode(
        mockBacnetConfig,
        'multistate-output-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'MultistateOutputNode',
        serializedData: {
          id: 'multistate-output-node',
          type: 'multistate-output',
          category: 'bacnet',
          label: 'VAV Box Mode',
          metadata: {
            pointId: 'MSO_001',
            objectType: 'multistate-output',
            objectId: 456,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'VAV Box Mode',
            discoveredProperties: {
              presentValue: 1,
              stateText: [null, 'Off', 'Heat', 'Cool'],
              numberOfStates: 3,
              description: 'VAV box operating mode',
            },
            position: { x: 150, y: 250 },
          },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with BacnetConfig', () => {
      const node = factory.createDataNodeFromBacnetConfig({
        config: mockBacnetConfig,
      }) as MultistateOutputNode

      expect(node.pointId).toBe('MSO_001')
      expect(node.objectType).toBe('multistate-output')
      expect(node.name).toBe('VAV Box Mode')
      expect(node.label).toBe('VAV Box Mode')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'MSO_004',
        objectType: 'multistate-output',
        objectId: 999,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Zone Mode',
        discoveredProperties: {
          presentValue: 0,
          stateText: ['Auto', 'Manual', 'Emergency'],
          numberOfStates: 3,
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as MultistateOutputNode

      expect(node.pointId).toBe('MSO_004')
      expect(node.name).toBe('Zone Mode')
      expect(node.objectId).toBe(999)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-multistate-output',
        type: 'multistate-output',
        category: 'bacnet',
        label: 'Restored Multistate Output',
        metadata: {
          pointId: 'MSO_999',
          objectType: 'multistate-output',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Multistate Output',
          discoveredProperties: {
            presentValue: 2,
            stateText: [null, 'State1', 'State2', 'State3'],
            numberOfStates: 3,
          },
          position: { x: 400, y: 500 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'MultistateOutputNode') {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'multistate-output'
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
        nodeType: 'MultistateOutputNode',
        serializedData,
        nodeFactory,
      }) as MultistateOutputNode

      expect(result.pointId).toBe('MSO_999')
      expect(result.name).toBe('Restored Multistate Output')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(2)
      expect(result.position).toEqual({ x: 400, y: 500 })
      expect(result.type).toBe('multistate-output')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new MultistateOutputNode(
        mockBacnetConfig,
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'MultistateOutputNode') {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'multistate-output'
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
      }) as MultistateOutputNode

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
