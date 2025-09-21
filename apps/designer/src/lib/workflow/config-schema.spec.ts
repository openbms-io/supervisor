import {
  VersionedWorkflowConfigSchema,
  WorkflowConfigSchema,
  EdgeDataSchema,
} from './config-schema'
import { NodeType, NodeCategory } from '@/types/infrastructure'

describe('Workflow Config Schema', () => {
  const baseMeta = { lastModified: '2025-09-19T10:30:00Z' }

  it('validates a constant node entry', () => {
    const cfg = {
      metadata: baseMeta,
      nodes: [
        {
          id: 'n1',
          type: 'logic.constant', // react-flow type string
          position: { x: 0, y: 0 },
          data: {
            nodeType: 'ConstantNode', // constructor name (compat)
            serializedData: {
              id: 'n1',
              type: NodeType.CONSTANT,
              category: NodeCategory.LOGIC,
              label: 'C',
              metadata: { value: 1, valueType: 'number' },
            },
          },
        },
      ],
      edges: [],
    }

    const result = WorkflowConfigSchema.safeParse(cfg)
    expect(result.success).toBe(true)
  })

  it('validates BACnet nodes for all object types', () => {
    const objectTypes: Array<{ nt: NodeType; ot: string }> = [
      { nt: NodeType.ANALOG_INPUT, ot: 'analog-input' },
      { nt: NodeType.ANALOG_OUTPUT, ot: 'analog-output' },
      { nt: NodeType.ANALOG_VALUE, ot: 'analog-value' },
      { nt: NodeType.BINARY_INPUT, ot: 'binary-input' },
      { nt: NodeType.BINARY_OUTPUT, ot: 'binary-output' },
      { nt: NodeType.BINARY_VALUE, ot: 'binary-value' },
      { nt: NodeType.MULTISTATE_INPUT, ot: 'multistate-input' },
      { nt: NodeType.MULTISTATE_OUTPUT, ot: 'multistate-output' },
      { nt: NodeType.MULTISTATE_VALUE, ot: 'multistate-value' },
    ]

    for (const { nt, ot } of objectTypes) {
      const cfg = {
        metadata: baseMeta,
        nodes: [
          {
            id: 'n1',
            type: `bacnet.${ot}`,
            position: { x: 0, y: 0 },
            data: {
              nodeType: 'AnalogInputNode', // value ignored by schema; factory uses it
              serializedData: {
                id: 'n1',
                type: nt,
                category: NodeCategory.BACNET,
                label: 'Point',
                metadata: {
                  pointId: 'pid-1',
                  objectType: ot,
                  objectId: 1,
                  supervisorId: 'sup-1',
                  controllerId: 'ctl-1',
                  name: 'P1',
                  discoveredProperties: { presentValue: 42 },
                },
              },
            },
          },
        ],
        edges: [],
      }

      const result = WorkflowConfigSchema.safeParse(cfg)
      expect(result.success).toBe(true)
    }
  })

  it('rejects invalid switch metadata', () => {
    const cfg = {
      metadata: baseMeta,
      nodes: [
        {
          id: 'n1',
          type: 'control-flow.switch',
          position: { x: 0, y: 0 },
          data: {
            nodeType: 'SwitchNode',
            serializedData: {
              id: 'n1',
              type: NodeType.SWITCH,
              category: NodeCategory.CONTROL_FLOW,
              label: 'Bad Switch',
              metadata: {
                condition: 'bad',
                threshold: 1,
                activeLabel: 'A',
                inactiveLabel: 'I',
              },
            },
          },
        },
      ],
      edges: [],
    }

    const result = WorkflowConfigSchema.safeParse(cfg)
    expect(result.success).toBe(false)
  })

  it('validates edge data with node categories and types', () => {
    const edge = {
      id: 'e1',
      source: 'n1',
      target: 'n2',
      sourceHandle: 'output',
      targetHandle: 'presentValue',
      data: {
        sourceData: {
          nodeId: 'n1',
          nodeCategory: NodeCategory.LOGIC,
          nodeType: NodeType.CONSTANT,
          handle: 'output',
        },
        targetData: {
          nodeId: 'n2',
          nodeCategory: NodeCategory.BACNET,
          nodeType: NodeType.ANALOG_OUTPUT,
          handle: 'presentValue',
        },
        isActive: true,
      },
    }
    const result = EdgeDataSchema.safeParse(edge.data)
    expect(result.success).toBe(true)
  })

  it('validates versioned workflow wrapper', () => {
    const versioned = {
      schema_info: {
        version: '1.0.0',
        schema_name: 'WorkflowConfig' as const,
        generated_at: '2025-09-19T10:30:00Z',
      },
      data: {
        metadata: baseMeta,
        nodes: [],
        edges: [],
      },
    }

    const result = VersionedWorkflowConfigSchema.safeParse(versioned)
    expect(result.success).toBe(true)
  })
})
