import { BinaryValueNode } from './binary-value-node'
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

describe('BinaryValueNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'BV_001',
    objectType: 'binary-value',
    objectId: 789,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'Occupancy Override',
    discoveredProperties: {
      presentValue: false,
      description: 'Manual occupancy override',
    },
    position: { x: 200, y: 300 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new BinaryValueNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('BV_001')
      expect(node.objectType).toBe('binary-value')
      expect(node.type).toBe('binary-value')
      expect(node.objectId).toBe(789)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('Occupancy Override')
      expect(node.label).toBe('Occupancy Override')
      expect(node.discoveredProperties).toEqual({
        presentValue: false,
        description: 'Manual occupancy override',
      })
      expect(node.position).toEqual({ x: 200, y: 300 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'BV_002',
        name: 'System Enable',
      }
      const node = new BinaryValueNode(config, 'custom-binary-value-id')

      expect(node.id).toBe('custom-binary-value-id')
      expect(node.pointId).toBe('BV_002')
      expect(node.name).toBe('System Enable')
      expect(node.label).toBe('System Enable')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'BV_003',
        objectType: 'binary-value',
        objectId: 456,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Manual Mode',
        discoveredProperties: {
          presentValue: true,
        },
      }
      const node = new BinaryValueNode(config)

      expect(node.objectId).toBe(456)
      expect(node.discoveredProperties.presentValue).toBe(true)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new BinaryValueNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'binary-value',
        category: 'bacnet',
        label: 'Occupancy Override',
        metadata: {
          pointId: 'BV_001',
          objectType: 'binary-value',
          objectId: 789,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'Occupancy Override',
          discoveredProperties: {
            presentValue: false,
            description: 'Manual occupancy override',
          },
          position: { x: 200, y: 300 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new BinaryValueNode(mockBacnetConfig, 'binary-value-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.BINARY_VALUE,
        serializedData: {
          id: 'binary-value-node',
          type: 'binary-value',
          category: 'bacnet',
          label: 'Occupancy Override',
          metadata: {
            pointId: 'BV_001',
            objectType: 'binary-value',
            objectId: 789,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'Occupancy Override',
            discoveredProperties: {
              presentValue: false,
              description: 'Manual occupancy override',
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
      }) as BinaryValueNode

      expect(node.pointId).toBe('BV_001')
      expect(node.objectType).toBe('binary-value')
      expect(node.name).toBe('Occupancy Override')
      expect(node.label).toBe('Occupancy Override')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'BV_004',
        objectType: 'binary-value',
        objectId: 321,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Alarm Reset',
        discoveredProperties: {
          presentValue: false,
          description: 'System alarm reset button',
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as BinaryValueNode

      expect(node.pointId).toBe('BV_004')
      expect(node.name).toBe('Alarm Reset')
      expect(node.objectId).toBe(321)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-binary-value',
        type: 'binary-value',
        category: 'bacnet',
        label: 'Restored Binary Value',
        metadata: {
          pointId: 'BV_999',
          objectType: 'binary-value',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Binary Value',
          discoveredProperties: {
            presentValue: true,
            description: 'Restored value',
          },
          position: { x: 500, y: 600 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.BINARY_VALUE) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'binary-value'
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
        nodeType: NodeType.BINARY_VALUE,
        serializedData,
        nodeFactory,
      }) as BinaryValueNode

      expect(result.pointId).toBe('BV_999')
      expect(result.name).toBe('Restored Binary Value')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(true)
      expect(result.position).toEqual({ x: 500, y: 600 })
      expect(result.type).toBe('binary-value')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new BinaryValueNode(mockBacnetConfig, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.BINARY_VALUE) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'binary-value'
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
      }) as BinaryValueNode

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
