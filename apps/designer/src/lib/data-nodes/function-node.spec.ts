import {
  FunctionNode,
  FunctionInput,
  FunctionNodeMetadata,
} from './function-node'
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

// Mock the QuickJS executor
jest.mock('@/lib/services/quickjs-executor', () => ({
  getQuickJSExecutor: jest.fn(() => ({
    execute: jest.fn().mockResolvedValue({ result: 42, logs: ['test log'] }),
  })),
}))

describe('FunctionNode', () => {
  describe('Constructor and basic properties', () => {
    it('should create node with basic properties', () => {
      const inputs: FunctionInput[] = [
        { id: 'input1', label: 'Value 1' },
        { id: 'input2', label: 'Value 2' },
      ]
      const node = new FunctionNode(
        'Test Function',
        {
          code: 'function execute(input1, input2) { return input1 + input2; }',
          inputs,
          timeout: 2000,
        },
        'explicit-test-id'
      )

      expect(node.id).toBe('explicit-test-id')
      expect(node.type).toBe('function')
      expect(node.label).toBe('Test Function')
      expect(node.metadata.code).toBe(
        'function execute(input1, input2) { return input1 + input2; }'
      )
      expect(node.metadata.inputs).toEqual(inputs)
      expect(node.metadata.timeout).toBe(2000)
      expect(node.category).toBe('logic')
    })

    it('should create node with provided id', () => {
      const node = new FunctionNode(
        'Test Function',
        undefined,
        'custom-function-id'
      )

      expect(node.id).toBe('custom-function-id')
      expect(node.type).toBe('function')
      expect(node.label).toBe('Test Function')
      expect(node.metadata.code).toBe(
        'function execute(input1) {\n  return input1;\n}'
      )
    })

    it('should handle different configurations', () => {
      const customNode = new FunctionNode('Custom Function', {
        code: 'function execute() { return true; }',
        inputs: [],
        timeout: 5000,
      })

      expect(customNode.metadata.code).toBe(
        'function execute() { return true; }'
      )
      expect(customNode.metadata.inputs).toEqual([])
      expect(customNode.metadata.timeout).toBe(5000)
    })
  })

  describe('Serialization', () => {
    it('should implement toSerializable correctly', () => {
      const inputs: FunctionInput[] = [{ id: 'input1', label: 'Input' }]
      const node = new FunctionNode(
        'My Function',
        {
          code: 'function execute(input1) { return input1 * 2; }',
          inputs,
          timeout: 3000,
        },
        'test-id-456'
      )

      const serialized = node.toSerializable()

      expect(serialized).toEqual({
        id: 'test-id-456',
        type: 'function',
        category: 'logic',
        label: 'My Function',
        metadata: {
          code: 'function execute(input1) { return input1 * 2; }',
          inputs: [{ id: 'input1', label: 'Input' }],
          timeout: 3000,
        },
      })
    })

    it('should serialize via serializeNodeData', () => {
      const inputs: FunctionInput[] = [
        { id: 'input1', label: 'A' },
        { id: 'input2', label: 'B' },
      ]
      const node = new FunctionNode(
        'Math Function',
        {
          code: 'function execute(input1, input2) { return Math.max(input1, input2); }',
          inputs,
          timeout: 1500,
        },
        'function-node'
      )

      const result = serializeNodeData(node)

      expect(result).toEqual({
        nodeType: 'FunctionNode',
        serializedData: {
          id: 'function-node',
          type: 'function',
          category: 'logic',
          label: 'Math Function',
          metadata: {
            code: 'function execute(input1, input2) { return Math.max(input1, input2); }',
            inputs: [
              { id: 'input1', label: 'A' },
              { id: 'input2', label: 'B' },
            ],
            timeout: 1500,
          },
        },
      })
    })
  })

  describe('Factory creation', () => {
    it('should create via factory with id', () => {
      const inputs: FunctionInput[] = [{ id: 'x', label: 'X Value' }]
      const node = factory.createFunctionNode({
        label: 'Factory Function',
        code: 'function execute(x) { return x * x; }',
        inputs,
        timeout: 4000,
        id: 'factory-test-id',
      })

      expect(node.label).toBe('Factory Function')
      expect((node as FunctionNode).metadata.code).toBe(
        'function execute(x) { return x * x; }'
      )
      expect((node as FunctionNode).metadata.inputs).toEqual(inputs)
      expect((node as FunctionNode).metadata.timeout).toBe(4000)
      expect(node.id).toBe('factory-test-id')
    })

    it('should create via factory with different parameters', () => {
      const node = factory.createFunctionNode({
        label: 'Factory Function 2',
        code: 'function execute() { return false; }',
        id: 'factory-function-id',
      })

      expect(node.label).toBe('Factory Function 2')
      expect((node as FunctionNode).metadata.code).toBe(
        'function execute() { return false; }'
      )
      expect(node.id).toBe('factory-function-id')
    })
  })

  describe('Deserialization', () => {
    it('should deserialize correctly via nodeFactory', () => {
      const serializedData = {
        id: 'deserialized-function',
        type: 'function',
        category: 'logic',
        label: 'Restored Function',
        metadata: {
          code: 'function execute(input1) { return !input1; }',
          inputs: [{ id: 'input1', label: 'Boolean Input' }],
          timeout: 2500,
        },
      }

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'FunctionNode') {
          const metadata = data.metadata as FunctionNodeMetadata
          return factory.createFunctionNode({
            label: data.label as string,
            code: metadata?.code,
            inputs: metadata?.inputs,
            timeout: metadata?.timeout,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const result = deserializeNodeData({
        nodeType: 'FunctionNode',
        serializedData,
        nodeFactory,
      }) as FunctionNode

      expect(result.id).toBe('deserialized-function')
      expect(result.label).toBe('Restored Function')
      expect(result.metadata.code).toBe(
        'function execute(input1) { return !input1; }'
      )
      expect(result.metadata.inputs).toEqual([
        { id: 'input1', label: 'Boolean Input' },
      ])
      expect(result.metadata.timeout).toBe(2500)
      expect(result.type).toBe('function')
    })
  })

  describe('Round-trip serialization', () => {
    it('should preserve all properties through serialize/deserialize cycle', () => {
      const inputs: FunctionInput[] = [
        { id: 'a', label: 'A' },
        { id: 'b', label: 'B' },
      ]
      const original = new FunctionNode(
        'Round Trip',
        {
          code: 'function execute(a, b) { return a && b; }',
          inputs,
          timeout: 6000,
        },
        'round-trip-id'
      )

      const serialized = serializeNodeData(original)

      const nodeFactory = (nodeType: string, data: Record<string, unknown>) => {
        if (nodeType === 'FunctionNode') {
          const metadata = data.metadata as FunctionNodeMetadata
          return factory.createFunctionNode({
            label: data.label as string,
            code: metadata?.code,
            inputs: metadata?.inputs,
            timeout: metadata?.timeout,
            id: data.id as string,
          })
        }
        throw new Error(`Unknown node type: ${nodeType}`)
      }

      const restored = deserializeNodeData({
        nodeType: serialized.nodeType,
        serializedData: serialized.serializedData,
        nodeFactory,
      }) as FunctionNode

      expect(restored.id).toBe(original.id)
      expect(restored.type).toBe(original.type)
      expect(restored.label).toBe(original.label)
      expect(restored.metadata.code).toBe(original.metadata.code)
      expect(restored.metadata.inputs).toEqual(original.metadata.inputs)
      expect(restored.metadata.timeout).toBe(original.metadata.timeout)
      expect(restored.category).toBe(original.category)
    })
  })
})
