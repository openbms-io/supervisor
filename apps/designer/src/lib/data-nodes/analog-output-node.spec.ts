import { AnalogOutputNode } from './analog-output-node'
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

describe('AnalogOutputNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'AO_001',
    objectType: 'analog-output',
    objectId: 456,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'Damper Position',
    discoveredProperties: {
      presentValue: 75.0,
      units: 'percent',
      description: 'VAV damper position',
    },
    position: { x: 150, y: 250 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new AnalogOutputNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('AO_001')
      expect(node.objectType).toBe('analog-output')
      expect(node.type).toBe('analog-output')
      expect(node.objectId).toBe(456)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('Damper Position')
      expect(node.label).toBe('Damper Position')
      expect(node.discoveredProperties).toEqual({
        presentValue: 75.0,
        units: 'percent',
        description: 'VAV damper position',
      })
      expect(node.position).toEqual({ x: 150, y: 250 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'AO_002',
        name: 'Fan Speed Control',
      }
      const node = new AnalogOutputNode(config, 'custom-analog-output-id')

      expect(node.id).toBe('custom-analog-output-id')
      expect(node.pointId).toBe('AO_002')
      expect(node.name).toBe('Fan Speed Control')
      expect(node.label).toBe('Fan Speed Control')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'AO_003',
        objectType: 'analog-output',
        objectId: 789,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Chilled Water Valve',
        discoveredProperties: {
          presentValue: 50.0,
          units: 'percent',
        },
      }
      const node = new AnalogOutputNode(config)

      expect(node.objectId).toBe(789)
      expect(node.discoveredProperties.presentValue).toBe(50.0)
      expect(node.discoveredProperties.units).toBe('percent')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new AnalogOutputNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'analog-output',
        category: 'bacnet',
        label: 'Damper Position',
        metadata: {
          pointId: 'AO_001',
          objectType: 'analog-output',
          objectId: 456,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'Damper Position',
          discoveredProperties: {
            presentValue: 75.0,
            units: 'percent',
            description: 'VAV damper position',
          },
          position: { x: 150, y: 250 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new AnalogOutputNode(mockBacnetConfig, 'analog-output-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'AnalogOutputNode',
        serializedData: {
          id: 'analog-output-node',
          type: 'analog-output',
          category: 'bacnet',
          label: 'Damper Position',
          metadata: {
            pointId: 'AO_001',
            objectType: 'analog-output',
            objectId: 456,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'Damper Position',
            discoveredProperties: {
              presentValue: 75.0,
              units: 'percent',
              description: 'VAV damper position',
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
      }) as AnalogOutputNode

      expect(node.pointId).toBe('AO_001')
      expect(node.objectType).toBe('analog-output')
      expect(node.name).toBe('Damper Position')
      expect(node.label).toBe('Damper Position')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'AO_004',
        objectType: 'analog-output',
        objectId: 999,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Heat Valve',
        discoveredProperties: {
          presentValue: 25.0,
          units: 'percent',
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as AnalogOutputNode

      expect(node.pointId).toBe('AO_004')
      expect(node.name).toBe('Heat Valve')
      expect(node.objectId).toBe(999)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-analog-output',
        type: 'analog-output',
        category: 'bacnet',
        label: 'Restored Analog Output',
        metadata: {
          pointId: 'AO_999',
          objectType: 'analog-output',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Analog Output',
          discoveredProperties: {
            presentValue: 85.5,
            units: 'percent',
          },
          position: { x: 400, y: 500 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'AnalogOutputNode') {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'analog-output'
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
        nodeType: 'AnalogOutputNode',
        serializedData,
        nodeFactory,
      }) as AnalogOutputNode

      expect(result.pointId).toBe('AO_999')
      expect(result.name).toBe('Restored Analog Output')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(85.5)
      expect(result.position).toEqual({ x: 400, y: 500 })
      expect(result.type).toBe('analog-output')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new AnalogOutputNode(mockBacnetConfig, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'AnalogOutputNode') {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'analog-output'
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
      }) as AnalogOutputNode

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
