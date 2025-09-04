'use client'

import { FlowNodeSchema, type FlowNode } from 'bms-schemas'

export function TestSchemaComponent() {
  // Test schema validation
  const testNode: FlowNode = {
    id: 'test-node-1',
    type: 'input.sensor',
    position: { x: 100, y: 200 },
    data: { label: 'Temperature Sensor' },
  }

  // Validate using Zod schema
  const validationResult = FlowNodeSchema.safeParse(testNode)

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="font-semibold mb-2">Schema Integration Test</h3>
      <div className="space-y-2">
        <p>
          <strong>Node ID:</strong> {testNode.id}
        </p>
        <p>
          <strong>Type:</strong> {testNode.type}
        </p>
        <p>
          <strong>Position:</strong> x={testNode.position.x}, y=
          {testNode.position.y}
        </p>
        <p>
          <strong>Validation:</strong>
          <span
            className={
              validationResult.success ? 'text-green-600' : 'text-red-600'
            }
          >
            {validationResult.success ? '✅ Valid' : '❌ Invalid'}
          </span>
        </p>
      </div>
    </div>
  )
}
