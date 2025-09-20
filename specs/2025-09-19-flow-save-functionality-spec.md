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

### Phase 7: Schema Validation Setup

- [ ] Create workflow-config-schema.ts with proper Zod schemas
- [ ] Define schemas for workflow metadata, nodes, edges
- [ ] Create versioned workflow config schema matching serializer structure
- [ ] Update projects API schema to use proper validation
- [ ] Replace z.object({}) with VersionedWorkflowConfigSchema
- [ ] Unit tests for schema validation

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
