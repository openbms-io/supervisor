'use client'

import { FlowNodeSchema, type FlowNode } from 'bms-schemas'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { CheckCircle, XCircle } from 'lucide-react'

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
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Schema Integration Test
          {validationResult.success ? (
            <CheckCircle className="h-5 w-5 text-green-600" />
          ) : (
            <XCircle className="h-5 w-5 text-red-600" />
          )}
        </CardTitle>
        <CardDescription>
          Testing Zod schema validation for FlowNode
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Node ID:</span>
            <Badge variant="outline">{testNode.id}</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Type:</span>
            <Badge variant="secondary">{testNode.type}</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Position:</span>
            <span className="text-sm text-muted-foreground">
              x={testNode.position.x}, y={testNode.position.y}
            </span>
          </div>
        </div>

        <Separator />

        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Validation Status:</span>
          <Badge
            variant={validationResult.success ? 'default' : 'destructive'}
            className="flex items-center gap-1"
          >
            {validationResult.success ? (
              <>
                <CheckCircle className="h-3 w-3" />
                Valid
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3" />
                Invalid
              </>
            )}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
