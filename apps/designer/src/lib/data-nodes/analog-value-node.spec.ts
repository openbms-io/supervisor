import { AnalogValueNode } from './analog-value-node'
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

describe('AnalogValueNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'AV_001',
    objectType: 'analog-value',
    objectId: 789,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'Zone Temperature Setpoint',
    discoveredProperties: {
      presentValue: 22.0,
      units: 'degrees-celsius',
      description: 'Zone temperature setpoint',
    },
    position: { x: 200, y: 300 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new AnalogValueNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('AV_001')
      expect(node.objectType).toBe('analog-value')
      expect(node.type).toBe('analog-value')
      expect(node.objectId).toBe(789)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('Zone Temperature Setpoint')
      expect(node.label).toBe('Zone Temperature Setpoint')
      expect(node.discoveredProperties).toEqual({
        presentValue: 22.0,
        units: 'degrees-celsius',
        description: 'Zone temperature setpoint',
      })
      expect(node.position).toEqual({ x: 200, y: 300 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'AV_002',
        name: 'Humidity Setpoint',
      }
      const node = new AnalogValueNode(config, 'custom-analog-value-id')

      expect(node.id).toBe('custom-analog-value-id')
      expect(node.pointId).toBe('AV_002')
      expect(node.name).toBe('Humidity Setpoint')
      expect(node.label).toBe('Humidity Setpoint')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'AV_003',
        objectType: 'analog-value',
        objectId: 456,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Pressure Setpoint',
        discoveredProperties: {
          presentValue: 100.0,
          units: 'pascals',
        },
      }
      const node = new AnalogValueNode(config)

      expect(node.objectId).toBe(456)
      expect(node.discoveredProperties.presentValue).toBe(100.0)
      expect(node.discoveredProperties.units).toBe('pascals')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new AnalogValueNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'analog-value',
        category: 'bacnet',
        label: 'Zone Temperature Setpoint',
        metadata: {
          pointId: 'AV_001',
          objectType: 'analog-value',
          objectId: 789,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'Zone Temperature Setpoint',
          discoveredProperties: {
            presentValue: 22.0,
            units: 'degrees-celsius',
            description: 'Zone temperature setpoint',
          },
          position: { x: 200, y: 300 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new AnalogValueNode(mockBacnetConfig, 'analog-value-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.ANALOG_VALUE,
        serializedData: {
          id: 'analog-value-node',
          type: 'analog-value',
          category: 'bacnet',
          label: 'Zone Temperature Setpoint',
          metadata: {
            pointId: 'AV_001',
            objectType: 'analog-value',
            objectId: 789,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'Zone Temperature Setpoint',
            discoveredProperties: {
              presentValue: 22.0,
              units: 'degrees-celsius',
              description: 'Zone temperature setpoint',
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
      }) as AnalogValueNode

      expect(node.pointId).toBe('AV_001')
      expect(node.objectType).toBe('analog-value')
      expect(node.name).toBe('Zone Temperature Setpoint')
      expect(node.label).toBe('Zone Temperature Setpoint')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'AV_004',
        objectType: 'analog-value',
        objectId: 321,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Flow Rate Setpoint',
        discoveredProperties: {
          presentValue: 50.0,
          units: 'liters-per-minute',
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as AnalogValueNode

      expect(node.pointId).toBe('AV_004')
      expect(node.name).toBe('Flow Rate Setpoint')
      expect(node.objectId).toBe(321)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-analog-value',
        type: 'analog-value',
        category: 'bacnet',
        label: 'Restored Analog Value',
        metadata: {
          pointId: 'AV_999',
          objectType: 'analog-value',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Analog Value',
          discoveredProperties: {
            presentValue: 45.5,
            units: 'percent',
          },
          position: { x: 500, y: 600 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.ANALOG_VALUE) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'analog-value'
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
        nodeType: NodeType.ANALOG_VALUE,
        serializedData,
        nodeFactory,
      }) as AnalogValueNode

      expect(result.pointId).toBe('AV_999')
      expect(result.name).toBe('Restored Analog Value')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(45.5)
      expect(result.position).toEqual({ x: 500, y: 600 })
      expect(result.type).toBe('analog-value')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new AnalogValueNode(mockBacnetConfig, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.ANALOG_VALUE) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'analog-value'
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
      }) as AnalogValueNode

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
