import { BinaryOutputNode } from './binary-output-node'
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

describe('BinaryOutputNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'BO_001',
    objectType: 'binary-output',
    objectId: 456,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'Fan Control',
    discoveredProperties: {
      presentValue: true,
      description: 'Exhaust fan control',
    },
    position: { x: 150, y: 250 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new BinaryOutputNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('BO_001')
      expect(node.objectType).toBe('binary-output')
      expect(node.type).toBe('binary-output')
      expect(node.objectId).toBe(456)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('Fan Control')
      expect(node.label).toBe('Fan Control')
      expect(node.discoveredProperties).toEqual({
        presentValue: true,
        description: 'Exhaust fan control',
      })
      expect(node.position).toEqual({ x: 150, y: 250 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'BO_002',
        name: 'Pump Control',
      }
      const node = new BinaryOutputNode(config, 'custom-binary-output-id')

      expect(node.id).toBe('custom-binary-output-id')
      expect(node.pointId).toBe('BO_002')
      expect(node.name).toBe('Pump Control')
      expect(node.label).toBe('Pump Control')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'BO_003',
        objectType: 'binary-output',
        objectId: 789,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Valve Control',
        discoveredProperties: {
          presentValue: false,
        },
      }
      const node = new BinaryOutputNode(config)

      expect(node.objectId).toBe(789)
      expect(node.discoveredProperties.presentValue).toBe(false)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new BinaryOutputNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'binary-output',
        category: 'bacnet',
        label: 'Fan Control',
        metadata: {
          pointId: 'BO_001',
          objectType: 'binary-output',
          objectId: 456,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'Fan Control',
          discoveredProperties: {
            presentValue: true,
            description: 'Exhaust fan control',
          },
          position: { x: 150, y: 250 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new BinaryOutputNode(mockBacnetConfig, 'binary-output-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'BinaryOutputNode',
        serializedData: {
          id: 'binary-output-node',
          type: 'binary-output',
          category: 'bacnet',
          label: 'Fan Control',
          metadata: {
            pointId: 'BO_001',
            objectType: 'binary-output',
            objectId: 456,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'Fan Control',
            discoveredProperties: {
              presentValue: true,
              description: 'Exhaust fan control',
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
      }) as BinaryOutputNode

      expect(node.pointId).toBe('BO_001')
      expect(node.objectType).toBe('binary-output')
      expect(node.name).toBe('Fan Control')
      expect(node.label).toBe('Fan Control')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'BO_004',
        objectType: 'binary-output',
        objectId: 999,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Light Control',
        discoveredProperties: {
          presentValue: false,
          description: 'Room lighting control',
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as BinaryOutputNode

      expect(node.pointId).toBe('BO_004')
      expect(node.name).toBe('Light Control')
      expect(node.objectId).toBe(999)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-binary-output',
        type: 'binary-output',
        category: 'bacnet',
        label: 'Restored Binary Output',
        metadata: {
          pointId: 'BO_999',
          objectType: 'binary-output',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Binary Output',
          discoveredProperties: {
            presentValue: false,
            description: 'Restored control',
          },
          position: { x: 400, y: 500 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'BinaryOutputNode') {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'binary-output'
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
        nodeType: 'BinaryOutputNode',
        serializedData,
        nodeFactory,
      }) as BinaryOutputNode

      expect(result.pointId).toBe('BO_999')
      expect(result.name).toBe('Restored Binary Output')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(false)
      expect(result.position).toEqual({ x: 400, y: 500 })
      expect(result.type).toBe('binary-output')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new BinaryOutputNode(mockBacnetConfig, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'BinaryOutputNode') {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'binary-output'
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
      }) as BinaryOutputNode

      expect(restored.pointId).toBe(original.pointId)
      expect(restored.objectType).toBe(original.objectType)
      expect(restored.type).toBe(original.type)
      expect(restored.objectId).toBe(original.objectId)
      expect(restored.supervisorId).toBe(original.supervisorId)
      expect(restored.controllerId).toBe(original.controllerId)
      expect(restored.name).toBe(original.name)
      expect(restored.label).toBe(original.label)
      expect(restored.discoveredProperties).toEqual(
        original.discoveredProperties
      )
      expect(restored.position).toEqual(original.position)
      expect(restored.category).toBe(original.category)
    })
  })
})
