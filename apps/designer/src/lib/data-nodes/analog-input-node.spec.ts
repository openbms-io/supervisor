import { AnalogInputNode } from './analog-input-node'
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

describe('AnalogInputNode', () => {
  const mockBacnetConfig: BacnetConfig = {
    pointId: 'AI_001',
    objectType: 'analog-input',
    objectId: 123,
    supervisorId: 'supervisor-1',
    controllerId: 'controller-1',
    name: 'Temperature Sensor',
    discoveredProperties: {
      presentValue: 22.5,
      units: 'degrees-celsius',
      description: 'Room temperature',
    },
    position: { x: 100, y: 200 },
  }

  describe('Constructor and basic properties', () => {
    it('should create node with BacnetConfig properties', () => {
      const node = new AnalogInputNode(mockBacnetConfig, 'explicit-test-id')

      expect(node.id).toBe('explicit-test-id')
      expect(node.pointId).toBe('AI_001')
      expect(node.objectType).toBe('analog-input')
      expect(node.type).toBe('analog-input')
      expect(node.objectId).toBe(123)
      expect(node.supervisorId).toBe('supervisor-1')
      expect(node.controllerId).toBe('controller-1')
      expect(node.name).toBe('Temperature Sensor')
      expect(node.label).toBe('Temperature Sensor')
      expect(node.discoveredProperties).toEqual({
        presentValue: 22.5,
        units: 'degrees-celsius',
        description: 'Room temperature',
      })
      expect(node.position).toEqual({ x: 100, y: 200 })
      expect(node.category).toBe('bacnet')
    })

    it('should create node with provided id', () => {
      const config: BacnetConfig = {
        ...mockBacnetConfig,
        pointId: 'AI_002',
        name: 'Pressure Sensor',
      }
      const node = new AnalogInputNode(config, 'custom-analog-input-id')

      expect(node.id).toBe('custom-analog-input-id')
      expect(node.pointId).toBe('AI_002')
      expect(node.name).toBe('Pressure Sensor')
      expect(node.label).toBe('Pressure Sensor')
    })

    it('should handle different configurations', () => {
      const config: BacnetConfig = {
        pointId: 'AI_003',
        objectType: 'analog-input',
        objectId: 456,
        supervisorId: 'supervisor-2',
        controllerId: 'controller-2',
        name: 'Humidity Sensor',
        discoveredProperties: {
          presentValue: 45.0,
          units: 'percent',
        },
      }
      const node = new AnalogInputNode(config)

      expect(node.objectId).toBe(456)
      expect(node.discoveredProperties.presentValue).toBe(45.0)
      expect(node.discoveredProperties.units).toBe('percent')
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const node = new AnalogInputNode(mockBacnetConfig, 'test-id-456')

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'analog-input',
        category: 'bacnet',
        label: 'Temperature Sensor',
        metadata: {
          pointId: 'AI_001',
          objectType: 'analog-input',
          objectId: 123,
          supervisorId: 'supervisor-1',
          controllerId: 'controller-1',
          name: 'Temperature Sensor',
          discoveredProperties: {
            presentValue: 22.5,
            units: 'degrees-celsius',
            description: 'Room temperature',
          },
          position: { x: 100, y: 200 },
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const node = new AnalogInputNode(mockBacnetConfig, 'analog-input-node')

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: NodeType.ANALOG_INPUT,
        serializedData: {
          id: 'analog-input-node',
          type: 'analog-input',
          category: 'bacnet',
          label: 'Temperature Sensor',
          metadata: {
            pointId: 'AI_001',
            objectType: 'analog-input',
            objectId: 123,
            supervisorId: 'supervisor-1',
            controllerId: 'controller-1',
            name: 'Temperature Sensor',
            discoveredProperties: {
              presentValue: 22.5,
              units: 'degrees-celsius',
              description: 'Room temperature',
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
      }) as AnalogInputNode

      expect(node.pointId).toBe('AI_001')
      expect(node.objectType).toBe('analog-input')
      expect(node.name).toBe('Temperature Sensor')
      expect(node.label).toBe('Temperature Sensor')
    })

    it('should create via factory with different config', () => {
      const config: BacnetConfig = {
        pointId: 'AI_004',
        objectType: 'analog-input',
        objectId: 789,
        supervisorId: 'supervisor-3',
        controllerId: 'controller-3',
        name: 'Flow Sensor',
        discoveredProperties: {
          presentValue: 150.0,
          units: 'liters-per-minute',
        },
      }
      const node = factory.createDataNodeFromBacnetConfig({
        config,
      }) as AnalogInputNode

      expect(node.pointId).toBe('AI_004')
      expect(node.name).toBe('Flow Sensor')
      expect(node.objectId).toBe(789)
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-analog-input',
        type: 'analog-input',
        category: 'bacnet',
        label: 'Restored Analog Input',
        metadata: {
          pointId: 'AI_999',
          objectType: 'analog-input',
          objectId: 999,
          supervisorId: 'supervisor-restored',
          controllerId: 'controller-restored',
          name: 'Restored Analog Input',
          discoveredProperties: {
            presentValue: 99.9,
            units: 'percent',
          },
          position: { x: 300, y: 400 },
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.ANALOG_INPUT) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'analog-input'
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
        nodeType: NodeType.ANALOG_INPUT,
        serializedData,
        nodeFactory,
      }) as AnalogInputNode

      expect(result.pointId).toBe('AI_999')
      expect(result.name).toBe('Restored Analog Input')
      expect(result.objectId).toBe(999)
      expect(result.discoveredProperties.presentValue).toBe(99.9)
      expect(result.position).toEqual({ x: 300, y: 400 })
      expect(result.type).toBe('analog-input')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const original = new AnalogInputNode(mockBacnetConfig, 'round-trip-id')

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === NodeType.ANALOG_INPUT) {
          const metadata = data.metadata as {
            pointId: string
            objectType: 'analog-input'
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
      }) as AnalogInputNode

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
