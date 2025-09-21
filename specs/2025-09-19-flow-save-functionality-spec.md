# Workflow Save Functionality Specification

**Document Version:** 1.0
**Date:** 2025-09-19
**Status:** Draft

## Overview

This specification defines the implementation of persistent workflow configuration storage in the BMS Supervisor Controller Designer app. Users will be able to save their visual programming workflows as part of project management, enabling persistence, sharing, and versioning of control logic configurations.

### Goals

- Enable users to save visual programming workflows to the database
- Provide seamless load/save experience integrated with existing project management
- Maintain data integrity for complex node configurations (timers, functions, schedules)
- Support future features like auto-save, versioning, and collaborative editing
- Follow TDD approach with comprehensive testing strategy

### Scope

- Workflow serialization and deserialization
- Integration with existing projects database schema
- Save/load UI components and user interactions
- API endpoints for workflow persistence
- Error handling and validation

## Current State Analysis

### Existing Infrastructure

1. **Database Schema** (`projects` table)

   - `workflow_config: text` field will store JSON workflow configurations
   - Full CRUD API endpoints available at `/api/projects`
   - Uses Drizzle ORM with SQLite for data persistence

2. **Workflow Management** (Zustand Store)

   - `useFlowStore` manages nodes and edges in memory
   - `DataGraph` class handles business logic and message routing
   - React Flow integration for visual representation

3. **Node Types** (Complex Data)
   - Function nodes with JavaScript code and dynamic inputs
   - Timer nodes with duration and scheduling
   - Schedule nodes with time ranges and day selections
   - BACnet nodes with device configurations
   - Logic nodes (calculation, comparison, constants)

### Current Limitations

- No persistence mechanism for workflows created in the canvas
- Projects store empty `workflow_config: '{}'` by default
- No UI indication of save status or unsaved changes
- No loading mechanism when opening existing projects

## Technical Specification

### Workflow Configuration Schema

```typescript
interface WorkflowConfig {
  version: string;
  metadata: {
    lastModified: string;
    createdBy?: string;
    description?: string;
  };
  nodes: Node[]; // React Flow Node type from toObject()
  edges: Edge[]; // React Flow Edge type from toObject()
}

// React Flow's built-in types include:
// Node: { id, type, position, data, ... }
// Edge: { id, source, target, sourceHandle?, targetHandle?, type?, data?, ... }
// All custom node data is preserved in the node.data field
```

### Serialization Strategy

#### React Flow Built-in Serialization

- Use `reactFlowInstance.toObject()` to serialize the complete workflow state
- Returns nodes, edges in React Flow's standard format
- All custom node data is preserved in `node.data` fields automatically
- No custom serialization logic needed for basic node/edge structure

#### Data Integrity

- Validate all node configurations before serialization using existing node validation
- Ensure backwards compatibility with version field
- Handle migration of legacy workflow formats

### Storage Implementation

#### Database Integration

- Utilize existing `projects.flow_config` field
- Store as JSON string with proper escaping
- Update `updated_at` timestamp on save operations
- Rename database field from `flow_config` to `workflow_config`
- Maintain transaction safety for concurrent access

#### API Endpoints (Existing)

- `PUT /api/projects/[id]` - Update project with workflow configuration
- `GET /api/projects/[id]` - Retrieve project with workflow configuration
- Extend existing validation schemas to include workflow structure

## Data Models

### Workflow Store Extensions

```typescript
interface FlowSlice {
  // Existing properties...

  // New save/load functionality
  isDirty: boolean;
  lastSaved?: Date;
  saveStatus: "saved" | "saving" | "error" | "unsaved";

  // Actions
  serializeWorkflow: () => WorkflowConfig;
  deserializeWorkflow: (config: WorkflowConfig) => void;
  saveWorkflow: (projectId: string) => Promise<void>;
  loadWorkflow: (projectId: string) => Promise<void>;
  markDirty: () => void;
  markClean: () => void;
}
```

### Validation Schema

```typescript
import { withVersion, SCHEMA_VERSION } from "@bms-schemas/version";

const WorkflowConfigBaseSchema = z.object({
  metadata: z.object({
    lastModified: z.string().datetime(),
    createdBy: z.string().optional(),
    description: z.string().optional(),
  }),
  nodes: z.array(z.any()), // React Flow Node schema
  edges: z.array(z.any()), // React Flow Edge schema
});

// Versioned schema using bms-schemas approach
const WorkflowConfigSchema = withVersion(
  WorkflowConfigBaseSchema,
  "WorkflowConfig",
);
```

## API Specification

### Extended Project Update Endpoint

**Endpoint:** `PUT /api/projects/[id]`

**Request Body:**

```json
{
  "name": "My Control Workflow",
  "description": "Temperature control logic",
  "workflow_config": {
    "version": "1.0",
    "metadata": {
      "lastModified": "2025-09-19T10:30:00Z"
    },
    "nodes": [...],
    "edges": [...]
  }
}
```

**Response:**

```json
{
  "success": true,
  "project": {
    "id": "uuid",
    "name": "My Control Workflow",
    "workflow_config": "{...}",
    "updated_at": "2025-09-19T10:30:00Z"
  }
}
```

### Error Handling

- **400 Bad Request**: Invalid workflow configuration schema
- **404 Not Found**: Project does not exist
- **413 Payload Too Large**: Workflow configuration exceeds size limits
- **500 Internal Server Error**: Database or serialization errors

## UI/UX Requirements

### Save Button Component

**Location:** WorkflowCanvas Panel (next to Execute button)
**States:**

- Default: "Save" button enabled when changes detected
- Saving: "Saving..." with loading spinner
- Saved: "Saved" with checkmark icon (3-second fade)
- Error: "Save Failed" with retry option

### Status Indicators

1. **Dirty State Indicator**

   - Small dot next to project name when unsaved changes exist
   - Clear visual distinction between saved/unsaved states

2. **Last Saved Timestamp**

   - "Last saved: 2 minutes ago" displayed in corner
   - Updates automatically, hidden when dirty

3. **Keyboard Shortcut**
   - Ctrl+S / Cmd+S to trigger save
   - Standard behavior users expect

### Load Workflow on Project Open

**Project Page Initialization:**

1. Load project data from API
2. Parse workflow_config JSON
3. Deserialize and populate workflow store
4. Initialize canvas with loaded nodes/edges
5. Set saved state and clear dirty flag

### Error Handling UI

- Toast notifications for save/load errors
- Retry mechanism for failed operations
- Graceful degradation when workflow config is corrupted
- Clear error messages with actionable next steps

## Implementation Phases

### Phase 1: Core Serialization

- [ ] Create `lib/workflow-serializer.ts` utility functions
- [ ] Implement React Flow toObject() integration
- [ ] Add validation schemas for workflow configuration
- [ ] Unit tests for serialization/deserialization

### Phase 2: Store Integration

- [ ] Extend FlowSlice with save/load methods
- [ ] Add dirty state tracking to all node update actions
- [ ] Implement serializeWorkflow() and deserializeWorkflow() methods
- [ ] Integration tests for store modifications

### Phase 3: API Integration

- [ ] Create `saveProject` and `loadProject` for API calls
- [ ] Extend project update API validation
- [ ] Add error handling and retry logic
- [ ] API integration tests [Skipping..]

### Phase 4: UI Implementation [Done]

- [ ] Add Save button to WorkflowCanvas Panel
- [ ] Add keyboard shortcut support
- [ ] Create loading and error state components. Use shadcn ui components.
- [ ] Trigger saveProject action on calling save.

### Phase 5: Load Workflow Implementation [Done]

- [ ] Modify project page to load existing workflows via loadProject action.
- [ ] Handle loading states and error conditions

### Phase 6: Polish & Testing [Skip]

- [ ] Auto-save implementation (debounced)
- [ ] Performance optimization for large workflows
- [ ] Cross-browser testing
- [ ] Accessibility improvements
- [ ] Documentation updates

### Phase 7: Schema Validation Setup [IN PROGRESS]

#### Overview

Replace `z.unknown()` validation in the projects API with comprehensive Zod schemas that properly validate the entire workflow configuration structure. This ensures data integrity and type safety throughout the save/load process.

#### Current Issues

1. Projects API uses `z.unknown()` for workflow_config field - no validation
2. Node types use string literals instead of centralized enum
3. No validation for node metadata structures
4. No validation for edge data structures
5. Serialized data structure is complex (double-wrapped by toSerializable and serializeNodeData)

#### Implementation Steps

##### Step 1: Create NodeType Enum

**File:** `/src/types/infrastructure.ts`

Add a centralized NodeType enum to replace string literals across all node implementations:

```typescript
export enum NodeType {
  // BACnet nodes (9 types)
  ANALOG_INPUT = "analog-input",
  ANALOG_OUTPUT = "analog-output",
  ANALOG_VALUE = "analog-value",
  BINARY_INPUT = "binary-input",
  BINARY_OUTPUT = "binary-output",
  BINARY_VALUE = "binary-value",
  MULTISTATE_INPUT = "multistate-input",
  MULTISTATE_OUTPUT = "multistate-output",
  MULTISTATE_VALUE = "multistate-value",

  // Logic nodes (4 types)
  CONSTANT = "constant",
  CALCULATION = "calculation",
  COMPARISON = "comparison",
  FUNCTION = "function",

  // Control flow nodes (3 types)
  SWITCH = "switch",
  TIMER = "timer",
  SCHEDULE = "schedule",

  // Command node (1 type)
  WRITE_SETPOINT = "write-setpoint",
}
```

Update NodeTypeString type to use the enum values.

##### Step 2: Update Node Classes to Use NodeType Enum

**Files to update:** All 17 node classes in `/src/lib/data-nodes/*.ts`

Replace string literals with enum values:

- `readonly type = 'constant' as const` → `readonly type = NodeType.CONSTANT`
- Import NodeType from '@/types/infrastructure'

**Files to update:**

- constant-node.ts
- calculation-node.ts
- comparison-node.ts
- function-node.ts
- switch-node.ts
- timer-node.ts
- schedule-node.ts
- write-setpoint-node.ts
- analog-input-node.ts
- analog-output-node.ts
- analog-value-node.ts
- binary-input-node.ts
- binary-output-node.ts
- binary-value-node.ts
- multistate-input-node.ts
- multistate-output-node.ts
- multistate-value-node.ts

##### Step 3: Update Serializer and Tests

**Files to update:**

- `/src/lib/workflow-serializer.ts` - Update createNodeFactory switch cases to use NodeType enum
- `/src/lib/workflow-serializer.spec.ts` - Update test expectations to use NodeType enum
- `/src/lib/workflow-serializer-basic.spec.ts` - Update test expectations to use NodeType enum

Example change in createNodeFactory:

```typescript
switch (nodeType) {
  case 'ConstantNode':  // Current
  // becomes
  case 'ConstantNode':  // Keep for backward compatibility with nodeType from constructor.name
```

##### Step 4: Create Comprehensive Workflow Config Schema

**New file:** `/src/lib/workflow-config-schema.ts`

```typescript
import { z } from "zod";
import { NodeType, NodeCategory, EdgeData } from "@/types/infrastructure";
import type { BacnetProperties, StatusFlags } from "@/types/bacnet-properties";
import type {
  ValueType,
  ConstantNodeMetadata,
  FunctionInput,
  FunctionNodeMetadata,
  TimerNodeMetadata,
  ScheduleNodeMetadata,
  DayOfWeek,
  CalculationOperation,
  ComparisonOperation,
} from "@/lib/data-nodes";
import type {
  WorkflowMetadata,
  SerializedNode,
  WorkflowConfig,
  VersionedWorkflowConfig,
  SerializedNodeData,
} from "./workflow-serializer";

// Reuse existing enums and types as Zod schemas
const NodeTypeSchema = z.nativeEnum(NodeType);
const NodeCategorySchema = z.nativeEnum(NodeCategory);

// Import existing type definitions and create matching Zod schemas
// These use z.ZodType to ensure the schemas match the TypeScript interfaces

// Value types for constant nodes (matching ValueType from constant-node.ts)
const ValueTypeSchema: z.ZodType<ValueType> = z.enum([
  "number",
  "boolean",
  "string",
]);

// Operations for calculation nodes (matching CalculationOperation from calculation-node.ts)
const CalculationOperationSchema: z.ZodType<CalculationOperation> = z.enum([
  "add",
  "subtract",
  "multiply",
  "divide",
  "average",
]);

// Operations for comparison nodes (matching ComparisonOperation from comparison-node.ts)
const ComparisonOperationSchema: z.ZodType<ComparisonOperation> = z.enum([
  "equals",
  "greater",
  "less",
  "greater-equal",
  "less-equal",
]);

// Control flow conditions for switch node
const SwitchConditionSchema = z.enum(["gt", "lt", "eq", "gte", "lte"]);

// Schedule days (matching DayOfWeek from schedule-node.ts)
const DayOfWeekSchema: z.ZodType<DayOfWeek> = z.enum([
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
  "Sun",
]);

// Function input schema (matching FunctionInput interface from function-node.ts)
const FunctionInputSchema: z.ZodType<FunctionInput> = z.object({
  id: z.string(),
  label: z.string(),
});

// BACnet properties schemas (matching interfaces from bacnet-properties.ts)
const StatusFlagsSchema: z.ZodType<StatusFlags> = z.object({
  inAlarm: z.boolean(),
  fault: z.boolean(),
  overridden: z.boolean(),
  outOfService: z.boolean(),
});

const BacnetPropertiesSchema: z.ZodType<BacnetProperties> = z.object({
  presentValue: z.union([z.number(), z.boolean(), z.string()]).optional(),
  statusFlags: StatusFlagsSchema.optional(),
  eventState: z.string().optional(),
  reliability: z.string().optional(),
  outOfService: z.boolean().optional(),
  units: z.string().optional(),
  description: z.string().optional(),
  minPresValue: z.number().optional(),
  maxPresValue: z.number().optional(),
  resolution: z.number().optional(),
  covIncrement: z.number().optional(),
  timeDelay: z.number().optional(),
  highLimit: z.number().optional(),
  lowLimit: z.number().optional(),
  deadband: z.number().optional(),
  priorityArray: z.array(z.number()).optional(),
  relinquishDefault: z.union([z.number(), z.boolean(), z.string()]).optional(),
  numberOfStates: z.number().optional(),
  stateText: z.array(z.union([z.string(), z.null()])).optional(),
});

// Node metadata schemas for each type (matching their respective interfaces)
const ConstantNodeMetadataSchema: z.ZodType<ConstantNodeMetadata> = z.object({
  value: z.union([z.number(), z.boolean(), z.string()]),
  valueType: ValueTypeSchema,
});

const CalculationNodeMetadataSchema = z.object({
  operation: CalculationOperationSchema,
});

const ComparisonNodeMetadataSchema = z.object({
  operation: ComparisonOperationSchema,
});

const FunctionNodeMetadataSchema: z.ZodType<FunctionNodeMetadata> = z.object({
  code: z.string(),
  inputs: z.array(FunctionInputSchema),
  timeout: z.number().optional(),
});

const SwitchNodeMetadataSchema = z.object({
  condition: SwitchConditionSchema,
  threshold: z.number(),
  activeLabel: z.string(),
  inactiveLabel: z.string(),
});

const TimerNodeMetadataSchema: z.ZodType<TimerNodeMetadata> = z.object({
  duration: z.number(),
});

const ScheduleNodeMetadataSchema: z.ZodType<ScheduleNodeMetadata> = z.object({
  startTime: z.string(),
  endTime: z.string(),
  days: z.array(DayOfWeekSchema),
});

const WriteSetpointNodeMetadataSchema = z.object({
  priority: z.number(),
});

// BACnet node metadata (used by all BACnet node types)
const BacnetNodeMetadataSchema = z.object({
  pointId: z.string(),
  objectType: z.string(),
  objectId: z.number(),
  supervisorId: z.string(),
  controllerId: z.string(),
  name: z.string(),
  discoveredProperties: BacnetPropertiesSchema,
  position: z
    .object({
      x: z.number(),
      y: z.number(),
    })
    .optional(),
});

// Discriminated union for serialized node data based on node type
const SerializedNodeDataContentSchema = z.discriminatedUnion("type", [
  // Logic nodes
  z.object({
    id: z.string(),
    type: z.literal(NodeType.CONSTANT),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: ConstantNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.CALCULATION),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: CalculationNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.COMPARISON),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: ComparisonNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.FUNCTION),
    category: z.literal(NodeCategory.LOGIC),
    label: z.string(),
    metadata: FunctionNodeMetadataSchema,
  }),
  // Control flow nodes
  z.object({
    id: z.string(),
    type: z.literal(NodeType.SWITCH),
    category: z.literal(NodeCategory.CONTROL_FLOW),
    label: z.string(),
    metadata: SwitchNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.TIMER),
    category: z.literal(NodeCategory.CONTROL_FLOW),
    label: z.string(),
    metadata: TimerNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.SCHEDULE),
    category: z.literal(NodeCategory.CONTROL_FLOW),
    label: z.string(),
    metadata: ScheduleNodeMetadataSchema,
  }),
  // Command node
  z.object({
    id: z.string(),
    type: z.literal(NodeType.WRITE_SETPOINT),
    category: z.literal(NodeCategory.COMMAND),
    label: z.string(),
    metadata: WriteSetpointNodeMetadataSchema,
  }),
  // BACnet nodes (all 9 types share same metadata structure)
  z.object({
    id: z.string(),
    type: z.literal(NodeType.ANALOG_INPUT),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.ANALOG_OUTPUT),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.ANALOG_VALUE),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.BINARY_INPUT),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.BINARY_OUTPUT),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.BINARY_VALUE),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.MULTISTATE_INPUT),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.MULTISTATE_OUTPUT),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
  z.object({
    id: z.string(),
    type: z.literal(NodeType.MULTISTATE_VALUE),
    category: z.literal(NodeCategory.BACNET),
    label: z.string(),
    metadata: BacnetNodeMetadataSchema,
  }),
]);

// SerializedNodeData wraps the node's toSerializable output
// Matches SerializedNodeData interface from node-serializer.ts
const SerializedNodeDataSchema: z.ZodType<SerializedNodeData> = z.object({
  nodeType: z.string(), // Constructor name like 'ConstantNode'
  serializedData: SerializedNodeDataContentSchema,
});

// Edge data schema (matching EdgeData interface from infrastructure.ts)
const EdgeDataSchema: z.ZodType<EdgeData> = z
  .object({
    sourceData: z.object({
      nodeId: z.string(),
      nodeCategory: NodeCategorySchema,
      nodeType: z.string(), // NodeTypeString
      handle: z.string().optional(),
    }),
    targetData: z.object({
      nodeId: z.string(),
      nodeCategory: NodeCategorySchema,
      nodeType: z.string(), // NodeTypeString
      handle: z.string().optional(),
    }),
    isActive: z.boolean().optional(),
  })
  .optional();

// Edge schema (React Flow edge with EdgeData)
const EdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  sourceHandle: z.string().optional(),
  targetHandle: z.string().optional(),
  type: z.string().optional(), // Edge type from EDGE_TYPES
  data: EdgeDataSchema,
});

// Workflow metadata schema (matching WorkflowMetadata interface from workflow-serializer.ts)
export const WorkflowMetadataSchema: z.ZodType<WorkflowMetadata> = z.object({
  lastModified: z.string().datetime(),
  createdBy: z.string().optional(),
  description: z.string().optional(),
});

// Serialized node schema (matching SerializedNode interface from workflow-serializer.ts)
export const SerializedNodeSchema: z.ZodType<SerializedNode> = z.object({
  id: z.string(),
  type: z.string(), // Node type string
  position: z.object({
    x: z.number(),
    y: z.number(),
  }),
  data: SerializedNodeDataSchema,
});

// Workflow config schema (matching WorkflowConfig interface from workflow-serializer.ts)
export const WorkflowConfigSchema: z.ZodType<WorkflowConfig> = z.object({
  metadata: WorkflowMetadataSchema,
  nodes: z.array(SerializedNodeSchema),
  edges: z.array(EdgeSchema),
});

// Version info schema (from bms-schemas Version type)
const VersionSchema = z.object({
  version: z.string(),
  compatibility: z.string(),
  schema_name: z.string(),
  generated_at: z.string().optional(),
});

// Versioned workflow config schema (matching VersionedWorkflowConfig type from workflow-serializer.ts)
export const VersionedWorkflowConfigSchema: z.ZodType<VersionedWorkflowConfig> =
  z.object({
    schema_info: VersionSchema,
    data: WorkflowConfigSchema,
  });

// Export for type inference
export type ValidatedWorkflowConfig = z.infer<
  typeof VersionedWorkflowConfigSchema
>;
```

##### Step 5: Update Projects API Schema

**File:** `/src/app/api/projects/schemas.ts`

```typescript
import { VersionedWorkflowConfigSchema } from "@/lib/workflow-config-schema";

// Update CreateProjectSchema
export const CreateProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Project name is required")
    .max(255, "Project name too long"),
  description: z.string().optional(),
  workflow_config: VersionedWorkflowConfigSchema.optional(),
});

// Update UpdateProjectSchema
export const UpdateProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Project name is required")
    .max(255, "Project name too long")
    .optional(),
  description: z.string().optional(),
  workflow_config: VersionedWorkflowConfigSchema.optional(),
});
```

##### Step 6: Update Workflow Serializer

**File:** `/src/lib/workflow-serializer.ts`

- Import schemas from workflow-config-schema.ts
- Remove duplicate local schema definitions
- Keep serialization/deserialization logic
- Export schemas from centralized location

#### Testing Requirements

1. **Schema Validation Tests**

   - Valid workflows with all node types pass validation
   - Invalid node metadata is rejected with clear errors
   - Edge data validation works correctly
   - Empty workflows are handled properly

2. **Backward Compatibility Tests**

   - Existing workflows load correctly with new enum
   - String literals in saved workflows map to enum values

3. **Integration Tests**
   - Save/load cycle works with new validation
   - API properly validates incoming workflow configs
   - Error messages are helpful for debugging

#### Benefits

1. **Type Safety**: Centralized NodeType enum ensures consistency
2. **Validation**: Comprehensive Zod schemas catch errors early
3. **Maintainability**: Single source of truth for node types
4. **Developer Experience**: Better IntelliSense and error messages
5. **Data Integrity**: Invalid workflows can't be saved to database

#### Migration Considerations

- Existing workflows in database use string literals
- createNodeFactory must handle both old string literals and new enum values
- Schema validation should accept both formats during transition period

## Testing Strategy

### Unit Tests

- **Workflow Serializer** (`lib/workflow-serializer.spec.ts`)

  - Test React Flow toObject() integration
  - Validate schema compliance
  - Test backwards compatibility
  - Error handling for malformed data

- **Workflow Store** (`store/slices/flow-slice.spec.ts`)
  - Test dirty state tracking
  - Validate save/load operations
  - Mock API calls and error scenarios

### Integration Tests

- **API Endpoints** (`api/projects/route.spec.ts`)

  - Test workflow config storage and retrieval
  - Validate request/response schemas
  - Test error conditions and edge cases

- **Workflow Loading** (`app/projects/[id]/page.spec.ts`)
  - Test project page initialization
  - Validate workflow store population
  - Test error recovery

### Test Data

- Sample workflow configurations for each node type
- Edge cases: empty workflows, large workflows, corrupted data
- Migration test data for version upgrades

## Security Considerations

### Input Validation

- Sanitize all flow configuration data before storage
- Validate node configurations against known schemas
- Prevent code injection in function node serialization
- Limit workflow configuration size to prevent DoS

### Data Sanitization

- Escape special characters in JSON serialization
- Validate UUIDs and handle ID conflicts
- Prevent XSS through malicious node labels/descriptions

### Access Control

- Ensure users can only save to projects they own
- Validate project ownership before workflow updates
- Rate limiting on save operations

## Future Enhancements

### Version Control (Phase 2)

- Track workflow configuration versions
- Implement rollback functionality
- Show diff views between versions
- Branch/merge capabilities for collaborative editing

### Auto-Save (Phase 2)

- Debounced auto-save every 30 seconds
- Background save with conflict resolution
- Local storage backup for reliability
- Visual indicators for auto-save status

### Collaborative Editing (Phase 3)

- Real-time workflow sharing between users
- Operational transformation for concurrent edits
- User presence indicators
- Comment and annotation system

### Performance Optimizations

- Incremental saving for large workflows
- Compression for workflow configurations
- Caching strategies for frequently accessed workflows
- Lazy loading of node configurations

### Export/Import

- Export workflows as standalone files
- Import workflows from other projects
- Template library for common patterns
- Integration with external tools

## Migration Strategy

### Existing Projects

- All existing projects have `workflow_config: '{}'`
- Database field rename from `flow_config` to `workflow_config` required
- UI should handle empty workflow configs gracefully
- Default to empty canvas when no saved workflow exists

### Database Migration

```sql
-- Rename column in projects table
ALTER TABLE projects RENAME COLUMN flow_config TO workflow_config;
```

### Schema Version Control

#### Version Management

- Use existing `bms-schemas/version.ts` system for version control
- Current schema version: `SCHEMA_VERSION` ("1.0.0")
- Compatibility: `SCHEMA_COMPATIBILITY` (">=1.0.0")
- Version metadata included automatically via `withVersion()` wrapper

#### Migration Strategy

- Schema changes require version bump in `packages/bms-schemas/src/version.ts`
- Migration logic handled by schema version compatibility checks
- Backwards compatibility maintained for supported versions
- Clear error messages for unsupported schema versions

#### Version Detection

```typescript
interface VersionedWorkflowConfig {
  schema_info: {
    version: string;
    compatibility: string;
    schema_name: string;
    generated_at?: string;
  };
  data: WorkflowConfig;
}
```

## Acceptance Criteria

### MVP Requirements

1. ✅ User can save current workflow to existing project
2. ✅ User can load saved workflow when opening project
3. ✅ All node types serialize/deserialize correctly using React Flow's toObject()
4. ✅ UI shows save status and dirty state
5. ✅ Error handling for failed save/load operations
6. ✅ Keyboard shortcut support (Ctrl+S)
7. ✅ Schema versioning using bms-schemas approach

### Success Metrics

- Save operation completes in <2 seconds for typical workflows
- Zero data loss in save/load operations
- 100% node type compatibility
- <5% error rate for save operations
- User can work offline and save when connection restored

## Dependencies

### Technical Dependencies

- Existing Zustand store architecture
- React Flow integration
- Drizzle ORM and SQLite database
- Next.js API routes
- Zod validation schemas

### Team Dependencies

- Designer app development team
- QA testing for flow persistence
- Product team for UX validation
- DevOps for deployment and monitoring

## Risks and Mitigation

### Technical Risks

1. **Large Workflow Performance**

   - Risk: Slow serialization/deserialization
   - Mitigation: Use React Flow's optimized toObject() method

2. **Data Corruption**

   - Risk: Invalid workflow configs break application
   - Mitigation: Comprehensive validation and error recovery

3. **Concurrent Save Conflicts**
   - Risk: Multiple users overwriting changes
   - Mitigation: Optimistic locking and conflict resolution

### Product Risks

1. **User Confusion**

   - Risk: Users lose work due to unclear save states
   - Mitigation: Clear UI indicators and user education

2. **Performance Impact**
   - Risk: Save operations slow down canvas interactions
   - Mitigation: Background saving and performance monitoring

## Conclusion

This specification provides a comprehensive roadmap for implementing workflow save functionality in the Designer app. The phased approach ensures steady progress while maintaining code quality and user experience. The foundation laid here will support future enhancements like version control, collaboration, and advanced project management features.

The implementation follows the project's TDD philosophy and integrates seamlessly with existing architecture patterns. Success will be measured by user adoption, data integrity, and performance metrics outlined in the acceptance criteria.
