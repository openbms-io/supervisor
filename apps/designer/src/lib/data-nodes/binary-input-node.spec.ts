import { BinaryInputNode } from './binary-input-node'
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

describe('BinaryInputNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'BI_001',
    objectType: 'binary-input',
    objectId: 123,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'Motion Detector',
    discoveredProperties: {
      presentValue: true,
      description: 'Occupancy motion sensor',
    },
    position: { x: 100, y: 200 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new BinaryInputNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('BI_001')
      expect(node.objectType).toBe('binary-input')
      expect(node.type).toBe('binary-input')
      expect(node.objectId).toBe(123)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('Motion Detector')
      expect(node.label).toBe('Motion Detector')
      expect(node.discoveredProperties).toEqual({
        presentValue: true,
        description: 'Occupancy motion sensor',
      })
      expect(node.position).toEqual({ x: 100, y: 200 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'BI_002',
        name: 'Door Contact',
      }
      const node = new BinaryInputNode(config, 'custom-binary-input-id')

      expect(node.id).toBe('custom-binary-input-id')
      expect(node.pointId).toBe('BI_002')
      expect(node.name).toBe('Door Contact')
      expect(node.label).toBe('Door Contact')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'BI_003',
        objectType: 'binary-input',
        objectId: 456,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Window Status',
        discoveredProperties: {
          presentValue: false,
        },
      }
      const node = new BinaryInputNode(config)

      expect(node.objectId).toBe(456)
      expect(node.discoveredProperties.presentValue).toBe(false)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new BinaryInputNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'binary-input',
        category: 'bacnet',
        label: 'Motion Detector',
        metadata: {
          pointId: 'BI_001',
          objectType: 'binary-input',
          objectId: 123,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'Motion Detector',
          discoveredProperties: {
            presentValue: true,
            description: 'Occupancy motion sensor',
          },
          position: { x: 100, y: 200 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new BinaryInputNode(mockBacnetConfig, 'binary-input-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.BINARY_INPUT,
        serializedData: {
          id: 'binary-input-node',
          type: 'binary-input',
          category: 'bacnet',
          label: 'Motion Detector',
          metadata: {
            pointId: 'BI_001',
            objectType: 'binary-input',
            objectId: 123,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'Motion Detector',
            discoveredProperties: {
              presentValue: true,
              description: 'Occupancy motion sensor',
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
      }) as BinaryInputNode

      expect(node.pointId).toBe('BI_001')
      expect(node.objectType).toBe('binary-input')
      expect(node.name).toBe('Motion Detector')
      expect(node.label).toBe('Motion Detector')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'BI_004',
        objectType: 'binary-input',
        objectId: 789,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Smoke Detector',
        discoveredProperties: {
          presentValue: false,
          description: 'Fire alarm detector',
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as BinaryInputNode

      expect(node.pointId).toBe('BI_004')
      expect(node.name).toBe('Smoke Detector')
      expect(node.objectId).toBe(789)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-binary-input',
        type: 'binary-input',
        category: 'bacnet',
        label: 'Restored Binary Input',
        metadata: {
          pointId: 'BI_999',
          objectType: 'binary-input',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Binary Input',
          discoveredProperties: {
            presentValue: true,
            description: 'Restored sensor',
          },
          position: { x: 300, y: 400 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.BINARY_INPUT) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'binary-input'
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
        nodeType: NodeType.BINARY_INPUT,
        serializedData,
        nodeFactory,
      }) as BinaryInputNode

      expect(result.pointId).toBe('BI_999')
      expect(result.name).toBe('Restored Binary Input')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(true)
      expect(result.position).toEqual({ x: 300, y: 400 })
      expect(result.type).toBe('binary-input')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new BinaryInputNode(mockBacnetConfig, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.BINARY_INPUT) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'binary-input'
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
      }) as BinaryInputNode

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
