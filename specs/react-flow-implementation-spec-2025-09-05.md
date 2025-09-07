# React Flow Implementation Specification

**Date**: 2025-09-05
**Project**: BMS Designer - Visual Flow Editor Integration

## 1. Overview

### 1.1 Goal

Integrate React Flow visual programming editor into the existing BMS Designer project management system, enabling users to create visual control flows for building management systems.

### 1.2 Key Features

- Visual drag-and-drop flow editor using React Flow
- Left panel with two tabs:
  1. **Palette**: Draggable atomic building blocks (BACnet objects + logical nodes + commands)
  2. **Supervisors**: IoT Supervisor management interface
- Integration with existing project CRUD system
- Flow configuration persistence in SQLite database
- Multiple input support for logical operations

### 1.3 Technical Stack

- React Flow v12 (@xyflow/react) for visual programming
- Zustand for flow state management
- **Graph data structure with adjacency list representation**
- **DFS/BFS algorithms for traversal and validation**
- Tailwind CSS for all styling (no custom CSS files)
- shadcn/ui components for UI consistency
- Existing project management hooks and API
- Mock API integration between Designer app and IoT Supervisor app

### 1.4 Architecture Principles

- **Separation of Concerns**: Graph logic separated from UI components
- **Graph-First Design**: Use proper graph data structures (adjacency list) for flow management
- **Algorithm-Based Validation**: DFS for cycle detection, topological sort for execution order
- **Type Safety**: Full TypeScript coverage with strict typing

## 2. File Naming Conventions

| Type            | Convention                          | Example                                |
| --------------- | ----------------------------------- | -------------------------------------- |
| Components      | PascalCase                          | `FlowEditorContainer.tsx`              |
| Node Components | [BACnetType]Node or [LogicType]Node | `AINode.tsx`, `CompareNode.tsx`        |
| Graph Classes   | PascalCase                          | `FlowGraph.ts`                         |
| Stores          | kebab-case                          | `flow-store.ts`                        |
| Tabs            | [Name]Tab                           | `PaletteTab.tsx`, `SupervisorsTab.tsx` |
| Types           | types.ts in component folder        | `components/types.ts`                  |
| Utils           | kebab-case                          | `graph-utils.ts`                       |

## 3. Directory Structure

```
apps/designer/src/
├── app/
│   └── projects/
│       └── [id]/
│           ├── page.tsx                        # Client component using container
│           └── components/
│               ├── FlowEditorContainer.tsx     # Main container with data fetching
│               ├── FlowEditor.tsx              # React Flow canvas component
│               ├── LeftPanel.tsx               # Tabbed left navigation
│               ├── types.ts                    # Component types and interfaces
│               ├── tabs/
│               │   ├── PaletteTab.tsx          # Draggable nodes palette tab
│               │   └── SupervisorsTab.tsx      # IoT Supervisor management tab
│               └── nodes/
│                   ├── index.ts                # Export all node types
│                   # BACnet Object Nodes (6)
│                   ├── AINode.tsx              # Analog Input
│                   ├── AONode.tsx              # Analog Output
│                   ├── BINode.tsx              # Binary Input
│                   ├── BONode.tsx              # Binary Output
│                   ├── AVNode.tsx              # Analog Value
│                   ├── BVNode.tsx              # Binary Value
│                   # Logical Nodes (5)
│                   ├── CompareNode.tsx         # Compare values
│                   ├── CalculateNode.tsx       # Mathematical operations
│                   ├── ConditionNode.tsx       # If/then logic
│                   ├── TimerNode.tsx           # Timer operations
│                   ├── ScheduleNode.tsx        # Schedule operations
│                   # Command Nodes (1)
│                   └── SetValueNode.tsx        # Set BACnet object value
├── lib/
│   └── flow-graph/
│       ├── FlowGraph.ts                       # Core graph data structure
│       ├── FlowValidator.ts                   # Validation logic
│       ├── FlowExecutor.ts                    # Execution order & simulation
│       ├── types.ts                           # Graph types and interfaces
│       ├── constants.ts                       # Connection rules and constants
│       └── utils.ts                           # Helper functions
└── stores/
    └── flow-store.ts                           # Zustand store with FlowGraph integration
```

## 4. Graph Data Structure Architecture

### 4.1 Core Concepts

The flow editor uses a **directed graph** data structure with:

- **Nodes**: Represent flow components (sensors, logic, actuators)
- **Edges**: Represent data flow between nodes
- **Adjacency List**: Efficient representation for sparse graphs
- **DFS/BFS**: Graph traversal for validation and execution order

### 4.2 Type-Safe Connection Rules with Composition Pattern

**Node-Based Connection System**: Each BACnet object IS a handle with built-in connection validation:

```typescript
// Handle type definitions - hybrid naming approach
type NodeTypeString =
  // BACnet objects - keep domain naming (familiar to BMS engineers)
  | "analog-input" // AI.presentValue → OUTPUT direction (provides sensor data)
  | "analog-output" // AO.presentValue → INPUT direction (receives control commands)
  | "binary-input" // BI.presentValue → OUTPUT direction (provides status data)
  | "binary-output" // BO.presentValue → INPUT direction (receives on/off commands)
  | "analog-value" // AV.presentValue → BIDIRECTIONAL (read/write virtual point)
  | "binary-value" // BV.presentValue → BIDIRECTIONAL (read/write virtual point)
  | "multistate-input"
  | "multistate-output"
  | "multistate-value"
  // Logic operations - clear data flow
  | "comparison" // BIDIRECTIONAL (compare inputs, output result)
  | "calculation" // BIDIRECTIONAL (math on inputs, output result)
  | "condition" // BIDIRECTIONAL (if-then logic)
  | "timer" // BIDIRECTIONAL (time-based operations)
  | "schedule" // BIDIRECTIONAL (schedule evaluation)
  // Terminal operations - clear action-based naming
  | "write-setpoint"; // INPUT direction (receives value to write as setpoint to BACnet property)

// Handle direction enum
enum NodeDirection {
  INPUT = "input", // Only receives data
  OUTPUT = "output", // Only sends data
  BIDIRECTIONAL = "bidirectional", // Can send or receive
}

// Base data node interface with dual identity
interface DataNode {
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity
  readonly type: NodeTypeString;
  readonly direction: NodeDirection;
  readonly metadata?: unknown;
  canConnectWith(other: DataNode): boolean;
}

// Pure BACnet configuration data
interface BacnetConfig {
  // BACnet object identification
  objectId: number;
  supervisorId: string;
  controllerId: string;

  // BACnet property data
  presentValue: number | boolean | string;
  units?: string;
  description: string;
  reliability: string;
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };

  // React Flow display properties
  label: string;
  position?: { x: number; y: number };
}

// Composition: BACnet data + DataNode behavior
interface BacnetInputOutput extends BacnetConfig, DataNode {
  // ID properties inherited from DataNode interface
  // readonly id: string     - Unique instance ID (UUID)
  // readonly pointId: string - Deterministic business identity
}
```

**Concrete Node Implementation Examples**:

```typescript
// AI Node - outputs sensor readings using composition pattern
class AnalogInputNode implements BacnetInputOutput {
  // BacnetConfig properties
  objectId: number;
  supervisorId: string;
  controllerId: string;
  presentValue: number;
  units?: string;
  description: string;
  reliability: string;
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };
  label: string;
  position?: { x: number; y: number };

  // DataNode properties
  readonly type = "analog-input" as const;
  readonly direction = NodeDirection.OUTPUT;
  readonly metadata = undefined; // Not needed - use direct properties

  // Computed property
  // Dual identity system
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity

  constructor(config: BacnetConfig, id?: string) {
    Object.assign(this, config);
    this.pointId = generateBACnetPointId(
      config.supervisorId,
      config.controllerId,
      config.objectId,
    );
    this.id = id || generateInstanceId();
    this.presentValue = config.presentValue as number;
  }

  canConnectWith(other: DataNode): boolean {
    // AI outputs data - can only connect to inputs or bidirectional
    if (other.direction === NodeDirection.OUTPUT) return false;

    // Type compatibility
    const compatibleTypes = [
      "analog-output",
      "analog-value",
      "comparison",
      "calculation",
      "write-setpoint",
    ];
    if (!compatibleTypes.includes(other.type)) return false;

    // Units compatibility using direct properties (no metadata needed)
    if (this.units && "units" in other && other.units) {
      return this.units === other.units;
    }

    return true;
  }
}

// AO Node - receives control commands (terminal input)
class AnalogOutputNode implements BacnetInputOutput {
  // BacnetConfig properties (same structure as AI)
  objectId: number;
  supervisorId: string;
  controllerId: string;
  presentValue: number;
  units?: string;
  description: string;
  reliability: string;
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };
  label: string;
  position?: { x: number; y: number };

  // DataNode properties - INPUT direction for outputs
  readonly type = "analog-output" as const;
  readonly direction = NodeDirection.INPUT;
  readonly metadata = undefined;

  // Dual identity system
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity

  constructor(config: BacnetConfig, id?: string) {
    Object.assign(this, config);
    this.pointId = generateBACnetPointId(
      config.supervisorId,
      config.controllerId,
      config.objectId,
    );
    this.id = id || generateInstanceId();
    this.presentValue = config.presentValue as number;
  }

  canConnectWith(other: DataNode): boolean {
    // AO is terminal - receives data but doesn't output to other nodes
    return false;
  }
}

// AV Node - bidirectional virtual point
class AnalogValueNode implements BacnetInputOutput {
  // BacnetConfig properties
  objectId: number;
  supervisorId: string;
  controllerId: string;
  presentValue: number;
  units?: string;
  description: string;
  reliability: string;
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };
  label: string;
  position?: { x: number; y: number };

  // DataNode properties - BIDIRECTIONAL for values
  readonly type = "analog-value" as const;
  readonly direction = NodeDirection.BIDIRECTIONAL;
  readonly metadata = undefined;

  // Dual identity system
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity

  constructor(config: BacnetConfig, id?: string) {
    Object.assign(this, config);
    this.pointId = generateBACnetPointId(
      config.supervisorId,
      config.controllerId,
      config.objectId,
    );
    this.id = id || generateInstanceId();
    this.presentValue = config.presentValue as number;
  }

  canConnectWith(other: DataNode): boolean {
    // AV is bidirectional - can connect to most types
    const compatibleTypes = [
      "analog-input",
      "analog-output",
      "analog-value",
      "comparison",
      "calculation",
      "condition",
      "write-setpoint",
    ];
    return compatibleTypes.includes(other.type);
  }
}
```

**Factory for Creating Node Instances**:

```typescript
// Deterministic UUID generation
import { v5 as uuidv5 } from "uuid";
const BACNET_NAMESPACE = "6ba7b810-9dad-11d1-80b4-00c04fd430c8";

function generateBACnetPointId(
  supervisorId: string,
  controllerId: string,
  objectId: number,
): string {
  const name = `${supervisorId}:${controllerId}:${objectId}`;
  return uuidv5(name, BACNET_NAMESPACE);
}

// BACnet Node Factory for creating concrete instances
class BACnetNodeFactory {
  static createAnalogInput(
    supervisorId: string,
    controllerId: string,
    objectId: number,
    presentValue: number,
    options?: {
      label?: string;
      units?: string;
      description?: string;
      position?: { x: number; y: number };
    },
    id?: string, // Optional instance ID
  ): AnalogInputNode {
    const config: BacnetConfig = {
      objectId,
      supervisorId,
      controllerId,
      presentValue,
      units: options?.units || "",
      description: options?.description || `Analog Input ${objectId}`,
      reliability: "no-fault-detected",
      statusFlags: {
        inAlarm: false,
        fault: false,
        overridden: false,
        outOfService: false,
      },
      label: options?.label || `AI-${objectId}`,
      position: options?.position,
    };
    return new AnalogInputNode(config, id);
  }

  static createAnalogOutput(
    supervisorId: string,
    controllerId: string,
    objectId: number,
    options?: {
      label?: string;
      units?: string;
      description?: string;
      position?: { x: number; y: number };
    },
    id?: string, // Optional instance ID
  ): AnalogOutputNode {
    const config: BacnetConfig = {
      objectId,
      supervisorId,
      controllerId,
      presentValue: 0,
      units: options?.units || "",
      description: options?.description || `Analog Output ${objectId}`,
      reliability: "no-fault-detected",
      statusFlags: {
        inAlarm: false,
        fault: false,
        overridden: false,
        outOfService: false,
      },
      label: options?.label || `AO-${objectId}`,
      position: options?.position,
    };
    return new AnalogOutputNode(config, id);
  }

  static createAnalogValue(
    supervisorId: string,
    controllerId: string,
    objectId: number,
    presentValue: number,
    options?: {
      label?: string;
      units?: string;
      description?: string;
      position?: { x: number; y: number };
    },
    id?: string, // Optional instance ID
  ): AnalogValueNode {
    const config: BacnetConfig = {
      objectId,
      supervisorId,
      controllerId,
      presentValue,
      units: options?.units || "",
      description: options?.description || `Analog Value ${objectId}`,
      reliability: "no-fault-detected",
      statusFlags: {
        inAlarm: false,
        fault: false,
        overridden: false,
        outOfService: false,
      },
      label: options?.label || `AV-${objectId}`,
      position: options?.position,
    };
    return new AnalogValueNode(config, id);
  }
}
```

**Connection Validation with Node Instances**:

```typescript
function validateConnection(
  source: BacnetInputOutput,
  target: BacnetInputOutput,
): boolean {
  // Check direction compatibility first
  const directionValid =
    (source.direction === NodeDirection.OUTPUT &&
      target.direction === NodeDirection.INPUT) ||
    source.direction === NodeDirection.BIDIRECTIONAL ||
    target.direction === NodeDirection.BIDIRECTIONAL;

  if (!directionValid) return false;

  // Check type compatibility
  return source.canConnectWith(target);
}
```

**Connection Matrix Visualization**:

| From \ To               | AI  | AO  | AV  | Comparison | Calculation | Write-Setpoint |
| ----------------------- | --- | --- | --- | ---------: | ----------- | :------------- |
| **AI (OUT)**            | ❌  | ❌  | ✅  |         ✅ | ✅          | ✅             |
| **AV (BI)**             | ❌  | ✅  | ✅  |         ✅ | ✅          | ✅             |
| **Comparison (BI)**     | ❌  | ✅  | ✅  |         ✅ | ✅          | ✅             |
| **Write-Setpoint (IN)** | ❌  | ❌  | ❌  |         ❌ | ❌          | ❌             |

**Benefits of Handle-Based System**:

- 🎯 **Semantic Clarity**: Handles represent actual data flow concepts
- 🔄 **Bidirectional Support**: Logic blocks can process data flexibly
- 📊 **BACnet Compliance**: Explicit input/output matches BACnet object semantics
- 🛡️ **Direction Safety**: Prevents data flowing backwards
- 🔧 **Self-Contained**: Each handle manages its own connection rules
- 📈 **Extensible**: Easy to add new handle types for specialized BMS functions

**Hybrid Naming Strategy**:
Our handle naming uses a hybrid approach that balances BMS domain familiarity with data flow clarity:

- **BACnet Objects**: Keep traditional naming (`analog-input`, `analog-output`) familiar to BMS engineers, even though direction seems counterintuitive to developers
- **Logic Operations**: Use clear data flow naming (`comparison`, `calculation`) that matches bidirectional processing
- **Terminal Operations**: Use action-based naming (`write-setpoint`) that clearly indicates the operation and direction

This avoids the confusion of `setpoint-output` (which would be INPUT direction) while maintaining BMS domain accuracy.

### 4.3 Dynamic Handle Generation and Validation

**Dynamic Multi-Input Handles**:

```typescript
// Nodes can have dynamic numbers of handles based on configuration
interface NodeConfig {
  id: string;
  type: NodeCategory;
  handles: DataNode[]; // Dynamically generated
}

// Compare node with configurable inputs
class CompareNodeConfig {
  static create(inputCount: number = 2): NodeConfig {
    const handles: DataNode[] = [];

    // Generate dynamic input handles
    for (let i = 1; i <= inputCount; i++) {
      handles.push(
        new ComparisonHandle(
          `input-${i}`, // Dynamic ID
          NodeDirection.BIDIRECTIONAL,
          { role: "input", index: i },
        ),
      );
    }

    // Add result output handle
    handles.push(
      new ComparisonHandle("result", NodeDirection.BIDIRECTIONAL, {
        role: "output",
      }),
    );

    return {
      id: `compare-${Date.now()}`,
      type: NodeCategory.LOGIC,
      handles,
    };
  }
}
```

**Enhanced Handle Classes with Metadata**:

```typescript
class ComparisonHandle implements DataNode {
  readonly type = "comparison" as const;
  readonly direction: NodeDirection;

  constructor(
    public id: string,
    direction: NodeDirection,
    public metadata?: {
      role?: "input" | "output";
      index?: number;
      acceptedUnits?: string[];
      dataRange?: [number, number];
    },
  ) {
    this.direction = direction;
  }

  canConnectWith(other: DataNode): boolean {
    // Context-aware validation based on role
    if (this.metadata?.role === "input") {
      // Input handles can accept analog outputs
      return (
        other.direction !== NodeDirection.INPUT &&
        ["analog-input", "analog-value", "calculation"].includes(other.type)
      );
    }

    if (this.metadata?.role === "output") {
      // Output handles can connect to other logic or commands
      return (
        other.direction !== NodeDirection.OUTPUT &&
        [
          "analog-output",
          "binary-output",
          "condition",
          "command-input",
        ].includes(other.type)
      );
    }

    // Generic bidirectional compatibility
    return [
      "analog-input",
      "analog-output",
      "binary-input",
      "binary-output",
    ].includes(other.type);
  }
}

class AnalogInputHandle implements DataNode {
  readonly type = "analog-input" as const;
  readonly direction = NodeDirection.OUTPUT;

  constructor(
    public id: string,
    public metadata?: {
      units?: string;
      range?: [number, number];
      objectId?: number;
      description?: string;
    },
  ) {}

  canConnectWith(other: DataNode): boolean {
    // Only connect to inputs or bidirectional handles
    if (other.direction === NodeDirection.OUTPUT) return false;

    // Type compatibility - analog inputs can connect to logic blocks and analog outputs
    const compatibleTypes = [
      "analog-output",
      "analog-value",
      "comparison",
      "calculation",
    ];
    if (!compatibleTypes.includes(other.type)) return false;

    // Units compatibility (if both specify units)
    if (this.metadata?.units && other.metadata?.units) {
      return this.metadata.units === other.metadata.units;
    }

    return true;
  }
}
```

**Universal Connection Validation**:

```typescript
function validateConnection(source: DataNode, target: DataNode): boolean {
  // Direction validation
  const directionValid =
    (source.direction === NodeDirection.OUTPUT &&
      target.direction === NodeDirection.INPUT) ||
    source.direction === NodeDirection.BIDIRECTIONAL ||
    target.direction === NodeDirection.BIDIRECTIONAL;

  if (!directionValid) {
    console.warn(
      `Direction mismatch: ${source.type}(${source.direction}) -> ${target.type}(${target.direction})`,
    );
    return false;
  }

  // Type-specific validation
  return source.canConnectWith(target);
}

// React Flow integration with DataNode validation
function onConnect(connection: Connection) {
  const sourceDataNode = getDataNode(connection.source); // Get DataNode from React Flow node
  const targetDataNode = getDataNode(connection.target);

  if (!sourceDataNode || !targetDataNode) {
    showError("Invalid node connection");
    return;
  }

  // Use DataNode business validation
  if (sourceDataNode.canConnectWith(targetDataNode)) {
    addEdge(connection);
  } else {
    showError(
      `Cannot connect ${sourceDataNode.type} to ${targetDataNode.type}`,
    );
  }
}
```

### 4.4 BACnet Object Architecture with Composition Pattern

**Separation of Concerns**: We separate pure BACnet configuration data from handle behavior using composition:

```typescript
// Pure BACnet configuration data (no behavior)
interface BacnetConfig {
  // BACnet object identification
  objectId: number;
  supervisorId: string;
  controllerId: string;

  // BACnet property data
  presentValue: number | boolean | string;
  units?: string;
  description: string;
  reliability:
    | "no-fault-detected"
    | "unreliable-other"
    | "over-range"
    | "under-range";
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };

  // Optional BACnet properties
  minPresValue?: number;
  maxPresValue?: number;
  resolution?: number;
  eventState?: "normal" | "fault" | "offnormal" | "high-limit" | "low-limit";
  updateInterval?: number;

  // React Flow display properties
  label: string;
  position?: { x: number; y: number };
}

// Data node behavior interface
interface DataNode {
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity
  readonly type: NodeTypeString;
  readonly direction: NodeDirection;
  readonly metadata?: unknown;
  canConnectWith(other: DataNode): boolean;
}

// Composition: BACnet data + DataNode behavior
interface BacnetInputOutput extends BacnetConfig, DataNode {
  // ID properties inherited from DataNode interface
  // readonly id: string     - Unique instance ID (UUID)
  // readonly pointId: string - Deterministic business identity
}

// UUID generation utilities
import { v4 as uuidv4, v5 as uuidv5 } from "uuid";
const BACNET_NAMESPACE = "6ba7b810-9dad-11d1-80b4-00c04fd430c8";

function generateBACnetPointId(
  supervisorId: string,
  controllerId: string,
  objectId: number,
): string {
  const name = `${supervisorId}:${controllerId}:${objectId}`;
  return uuidv5(name, BACNET_NAMESPACE);
}

function generateInstanceId(): string {
  return uuidv4();
}

// Concrete node classes implementing composition pattern
class AnalogInputNode implements BacnetInputOutput {
  // BacnetConfig properties
  objectId: number;
  supervisorId: string;
  controllerId: string;
  presentValue: number;
  units?: string;
  description: string;
  reliability:
    | "no-fault-detected"
    | "unreliable-other"
    | "over-range"
    | "under-range";
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };
  minPresValue?: number;
  maxPresValue?: number;
  resolution?: number;
  eventState?: "normal" | "fault" | "offnormal" | "high-limit" | "low-limit";
  updateInterval?: number;
  label: string;
  position?: { x: number; y: number };

  // DataNode properties
  readonly type = "analog-input" as const;
  readonly direction = NodeDirection.OUTPUT;
  readonly metadata = undefined; // Not needed - use BacnetConfig properties directly

  // Dual identity system
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity

  constructor(config: BacnetConfig, id?: string) {
    // Copy all configuration properties
    Object.assign(this, config);

    // Generate IDs
    this.pointId = generateBACnetPointId(
      config.supervisorId,
      config.controllerId,
      config.objectId,
    );
    this.id = id || generateInstanceId();

    // Ensure presentValue is number for AI
    this.presentValue = config.presentValue as number;
  }

  canConnectWith(other: DataNode): boolean {
    // Only connect to inputs or bidirectional handles
    if (other.direction === NodeDirection.OUTPUT) return false;

    // Type compatibility
    const compatibleTypes = [
      "analog-output",
      "analog-value",
      "comparison",
      "calculation",
    ];
    if (!compatibleTypes.includes(other.type)) return false;

    // Units compatibility using direct properties (no metadata needed)
    if (this.units && "units" in other && other.units) {
      return this.units === other.units;
    }

    return true;
  }
}

class AnalogOutputNode implements BacnetInputOutput {
  // BacnetConfig properties (same structure as AI)
  objectId: number;
  supervisorId: string;
  controllerId: string;
  presentValue: number;
  units?: string;
  description: string;
  reliability:
    | "no-fault-detected"
    | "unreliable-other"
    | "over-range"
    | "under-range";
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };
  minPresValue?: number;
  maxPresValue?: number;
  resolution?: number;
  eventState?: "normal" | "fault" | "offnormal" | "high-limit" | "low-limit";
  updateInterval?: number;
  label: string;
  position?: { x: number; y: number };

  // DataNode properties - INPUT direction for outputs
  readonly type = "analog-output" as const;
  readonly direction = NodeDirection.INPUT;
  readonly metadata = undefined;

  // Dual identity system
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity

  constructor(config: BacnetConfig, id?: string) {
    Object.assign(this, config);
    this.pointId = generateBACnetPointId(
      config.supervisorId,
      config.controllerId,
      config.objectId,
    );
    this.id = id || generateInstanceId();
    this.presentValue = config.presentValue as number;
  }

  canConnectWith(other: DataNode): boolean {
    // AO receives data, so it can connect to outputs or bidirectional
    return other.direction !== NodeDirection.INPUT;
  }
}

class AnalogValueNode implements BacnetInputOutput {
  // BacnetConfig properties (same structure)
  objectId: number;
  supervisorId: string;
  controllerId: string;
  presentValue: number;
  units?: string;
  description: string;
  reliability:
    | "no-fault-detected"
    | "unreliable-other"
    | "over-range"
    | "under-range";
  statusFlags: {
    inAlarm: boolean;
    fault: boolean;
    overridden: boolean;
    outOfService: boolean;
  };
  minPresValue?: number;
  maxPresValue?: number;
  resolution?: number;
  eventState?: "normal" | "fault" | "offnormal" | "high-limit" | "low-limit";
  updateInterval?: number;
  label: string;
  position?: { x: number; y: number };

  // DataNode properties - BIDIRECTIONAL for values
  readonly type = "analog-value" as const;
  readonly direction = NodeDirection.BIDIRECTIONAL;
  readonly metadata = undefined;

  // Dual identity system
  readonly id: string; // Unique instance ID (UUID)
  readonly pointId: string; // Deterministic business identity

  constructor(config: BacnetConfig, id?: string) {
    Object.assign(this, config);
    this.pointId = generateBACnetPointId(
      config.supervisorId,
      config.controllerId,
      config.objectId,
    );
    this.id = id || generateInstanceId();
    this.presentValue = config.presentValue as number;
  }

  canConnectWith(other: DataNode): boolean {
    // AV is bidirectional - can connect to most types
    const compatibleTypes = [
      "analog-input",
      "analog-output",
      "analog-value",
      "comparison",
      "calculation",
      "condition",
      "write-setpoint",
    ];
    return compatibleTypes.includes(other.type);
  }
}
```

**Usage Examples**:

```typescript
// Create BACnet configuration
const tempSensorConfig: BacnetConfig = {
  objectId: 1001,
  supervisorId: "building1",
  controllerId: "hvac1",
  presentValue: 23.5,
  units: "°C",
  description: "Temperature sensor in Zone 1",
  reliability: "no-fault-detected",
  statusFlags: {
    inAlarm: false,
    fault: false,
    overridden: false,
    outOfService: false,
  },
  label: "Zone 1 Temperature",
  position: { x: 100, y: 200 },
};

// Create node instance
const tempSensor = new AnalogInputNode(tempSensorConfig);

console.log(tempSensor.id); // "f47ac10b-58cc-4372-a567-0e02b2c3d479" (consistent UUID)
console.log(tempSensor.type); // "analog-input"
console.log(tempSensor.direction); // "output"
console.log(tempSensor.label); // "Zone 1 Temperature"

// Same configuration always produces same ID
const tempSensor2 = new AnalogInputNode(tempSensorConfig);
console.log(tempSensor.id === tempSensor2.id); // true

// React Flow integration
const reactFlowNode = {
  id: tempSensor.id,
  type: "bacnet.ai",
  position: tempSensor.position || { x: 0, y: 0 },
  data: tempSensor, // Node IS the data
};
```

**Benefits of Composition Pattern**:

- 🔧 **Separation of Concerns**: BacnetConfig is pure data, DataNode is pure behavior
- 🎯 **Clean Construction**: Constructor takes exactly what it needs (BacnetConfig)
- ♻️ **Reusable Configuration**: BacnetConfig can be used independently for storage, APIs
- 🆔 **Consistent IDs**: Deterministic UUID generation from BACnet coordinates
- 🛡️ **Type Safety**: TypeScript ensures both interfaces are properly implemented
- 📊 **Direct Property Access**: No metadata needed - use BACnet properties directly

**Connection Validation with Composition Pattern**:

```typescript
// Connection validation uses node properties directly
const tempSensor = new AnalogInputNode(tempSensorConfig);
const valveControl = new AnalogOutputNode(valveConfig);

// Type-safe connection validation
const canConnect = tempSensor.canConnectWith(valveControl);
console.log(canConnect); // false (OUTPUT cannot connect to INPUT)

// Through logic node
const comparisonNode = new ComparisonNode(comparisonConfig);
const tempToComparison = tempSensor.canConnectWith(comparisonNode); // true
const comparisonToValve = comparisonNode.canConnectWith(valveControl); // true
```

**Multiple Input Support**: Logic nodes accept connections from multiple BACnet objects through React Flow's edge system. Each connection represents data flowing from one node to another:

```typescript
// Example: Comparison Logic Node with React Flow Integration
export function ComparisonNodeComponent({ data, selected }: NodeProps<ComparisonLogicNode>) {
  const [inputConnections, setInputConnections] = useState<Edge[]>([])

  return (
    <div className={`comparison-node ${selected ? 'selected' : ''}`}>
      <div className="node-header">
        <GitCompare className="w-4 h-4" />
        <span>{data.label}</span>
      </div>

      {/* Multiple input handles for React Flow connections */}
      <Handle
        type="target"
        position={Position.Left}
        id="input-a"
        style={{ top: '30%', backgroundColor: '#3b82f6' }}
        className="w-3 h-3 border-2 border-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="input-b"
        style={{ top: '70%', backgroundColor: '#3b82f6' }}
        className="w-3 h-3 border-2 border-white"
      />

      <div className="node-content p-2">
        <span className="text-xs font-medium">{data.operation}</span>
        {data.threshold && (
          <div className="text-xs text-gray-600">threshold: {data.threshold}</div>
        )}
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="result"
        className="w-3 h-3 bg-green-500 border-2 border-white"
      />
    </div>
  )
}

// Data Flow Through React Flow Edges:
// [AnalogInputNode] ──edge──> [ComparisonLogicNode] ──edge──> [AnalogOutputNode]
//
// React Flow manages connections via edges array:
const edges = [
  {
    id: 'ai-to-compare-a',
    source: 'temperature-ai-01',  // AnalogInputNode.id
    sourceHandle: 'output',
    target: 'temp-compare-logic',  // ComparisonLogicNode.id
    targetHandle: 'input-a'
  },
  {
    id: 'av-to-compare-b',
    source: 'setpoint-av-01',     // AnalogValueNode.id
    sourceHandle: 'output',
    target: 'temp-compare-logic', // ComparisonLogicNode.id
    targetHandle: 'input-b'
  },
  {
    id: 'compare-to-ao',
    source: 'temp-compare-logic', // ComparisonLogicNode.id
    sourceHandle: 'result',
    target: 'hvac-output-01',     // AnalogOutputNode.id
    targetHandle: 'input'
  }
]
```

**Node-Based Connection Validation**: Each node validates its own connections using the composition pattern:

```typescript
// Factory creates instances that handle their own validation
const tempSensor = BACnetNodeFactory.createAnalogInput(
  "super-01",
  "ctrl-01",
  101,
  { label: "Temperature" },
);
const setpoint = BACnetNodeFactory.createAnalogValue(
  "super-01",
  "ctrl-01",
  201,
  { label: "Setpoint" },
);
const comparison = new ComparisonLogicNode("super-01", "ctrl-01", "greater", {
  label: "Temp > Setpoint",
});
const hvacOutput = BACnetNodeFactory.createAnalogOutput(
  "super-01",
  "ctrl-01",
  301,
  { label: "HVAC Control" },
);

// Validation uses node instances directly
function validateEdgeConnection(
  source: BacnetInputOutput,
  target: BacnetInputOutput,
): boolean {
  return source.canConnectWith(target);
}

// React Flow onConnect handler
function onConnect(connection: Connection) {
  const sourceNode = nodes.find(
    (n) => n.id === connection.source,
  ) as BacnetInputOutput;
  const targetNode = nodes.find(
    (n) => n.id === connection.target,
  ) as BacnetInputOutput;

  if (validateEdgeConnection(sourceNode, targetNode)) {
    setEdges((edges) => [
      ...edges,
      {
        id: `${connection.source}-to-${connection.target}`,
        ...connection,
      },
    ]);
  } else {
    showError(`Cannot connect ${sourceNode.type} to ${targetNode.type}`);
  }
}

// ✅ Valid connections using composition pattern
const tempAI = BACnetNodeFactory.createAnalogInput("super-01", "ctrl-01", 101);
const hvacAO = BACnetNodeFactory.createAnalogOutput("super-01", "ctrl-01", 201);
const comparison = new ComparisonLogicNode("super-01", "ctrl-01", "greater");

// Node-based validation (no separate handle types needed)
const isValid1 = tempAI.canConnectWith(comparison); // true - AI can connect to logic
const isValid2 = comparison.canConnectWith(hvacAO); // true - logic can connect to AO
const isValid3 = hvacAO.canConnectWith(tempAI); // false - output can't connect to output

// React Flow integration validates nodes directly
function isValidConnection(connection: Connection): boolean {
  const source = getNodeById(connection.source) as BacnetInputOutput;
  const target = getNodeById(connection.target) as BacnetInputOutput;
  return source.canConnectWith(target);
}
```

**Multi-Input Logic Examples**:

- **Temperature Control**: AI.presentValue + AV.setpoint → Comparison → AO.presentValue
- **Fault Detection**: Multiple AI.reliability → Logic → BO.alarm
- **Scheduled Control**: Timer.output + Schedule.active → Logic → Multiple outputs

**Benefits of Type-Safe System**:

- **Compile-time validation**: TypeScript catches invalid connections during development
- **No runtime string manipulation**: Direct enum comparisons are faster and safer
- **Autocomplete support**: IDEs provide accurate suggestions for node types and handles
- **Refactoring safety**: Renaming node types updates all references automatically
- **Performance improvement**: No regex matching or string parsing at runtime

### 4.4 FlowGraph Class Specification

```typescript
export class DataGraph {
  // Core graph structure - adjacency list with instance IDs
  private adjacencyList: Map<string, Set<string>>; // sourceId -> Set<targetIds>
  private reverseAdjacencyList: Map<string, Set<string>>; // targetId -> Set<sourceIds>
  private nodeIndex: Map<string, DataNode>; // instanceId -> DataNode object

  constructor() {
    this.adjacencyList = new Map();
    this.reverseAdjacencyList = new Map();
    this.nodeIndex = new Map();
  }

  // Node operations - work with DataNode objects
  addNode(node: DataNode): void {
    this.nodeIndex.set(node.id, node);
    if (!this.adjacencyList.has(node.id)) {
      this.adjacencyList.set(node.id, new Set());
    }
    if (!this.reverseAdjacencyList.has(node.id)) {
      this.reverseAdjacencyList.set(node.id, new Set());
    }
  }

  removeNode(nodeId: string): void {
    const node = this.nodeIndex.get(nodeId);
    if (!node) return;

    // Remove all connections involving this node
    this.adjacencyList.get(nodeId)?.forEach((targetId) => {
      this.reverseAdjacencyList.get(targetId)?.delete(nodeId);
    });

    this.reverseAdjacencyList.get(nodeId)?.forEach((sourceId) => {
      this.adjacencyList.get(sourceId)?.delete(nodeId);
    });

    // Remove the node
    this.nodeIndex.delete(nodeId);
    this.adjacencyList.delete(nodeId);
    this.reverseAdjacencyList.delete(nodeId);
  }

  getNode(nodeId: string): DataNode | undefined {
    return this.nodeIndex.get(nodeId);
  }

  getAllNodes(): DataNode[] {
    return Array.from(this.nodeIndex.values());
  }

  // Connection operations using business logic validation
  addConnection(sourceId: string, targetId: string): boolean {
    const source = this.nodeIndex.get(sourceId);
    const target = this.nodeIndex.get(targetId);

    if (!source || !target) return false;

    // Use DataNode business validation
    if (!source.canConnectWith(target)) return false;

    // Add connection to adjacency lists
    this.adjacencyList.get(sourceId)?.add(targetId);
    this.reverseAdjacencyList.get(targetId)?.add(sourceId);
    return true;
  }

  removeConnection(sourceId: string, targetId: string): void {
    this.adjacencyList.get(sourceId)?.delete(targetId);
    this.reverseAdjacencyList.get(targetId)?.delete(sourceId);
  }

  hasConnection(sourceId: string, targetId: string): boolean {
    return this.adjacencyList.get(sourceId)?.has(targetId) || false;
  }

  getAllEdges(): Array<{ source: DataNode; target: DataNode }> {
    const edges: Array<{ source: DataNode; target: DataNode }> = [];
    for (const [sourceId, targetIds] of this.adjacencyList) {
      const source = this.nodeIndex.get(sourceId)!;
      for (const targetId of targetIds) {
        const target = this.nodeIndex.get(targetId)!;
        edges.push({ source, target });
      }
    }
    return edges;
  }

  // Business layer graph traversal algorithms
  dfs(startNodeId: string, visited?: Set<string>): string[] {
    const result: string[] = [];
    const visitedSet = visited || new Set();

    if (visitedSet.has(startNodeId)) return result;
    visitedSet.add(startNodeId);
    result.push(startNodeId);

    const neighbors = this.adjacencyList.get(startNodeId) || new Set();
    for (const neighborId of neighbors) {
      result.push(...this.dfs(neighborId, visitedSet));
    }

    return result;
  }

  bfs(startNodeId: string): string[] {
    const result: string[] = [];
    const visited = new Set<string>();
    const queue = [startNodeId];

    while (queue.length > 0) {
      const nodeId = queue.shift()!;
      if (visited.has(nodeId)) continue;

      visited.add(nodeId);
      result.push(nodeId);

      const neighbors = this.adjacencyList.get(nodeId) || new Set();
      for (const neighborId of neighbors) {
        if (!visited.has(neighborId)) {
          queue.push(neighborId);
        }
      }
    }

    return result;
  }

  // Control system specific operations
  getExecutionOrder(): string[] {
    // Topological sort for control system execution order
    const result: string[] = [];
    const visited = new Set<string>();
    const stack: string[] = [];

    for (const nodeId of this.nodeIndex.keys()) {
      if (!visited.has(nodeId)) {
        this.topologicalSortUtil(nodeId, visited, stack);
      }
    }

    return stack.reverse();
  }

  private topologicalSortUtil(
    nodeId: string,
    visited: Set<string>,
    stack: string[],
  ): void {
    visited.add(nodeId);

    const neighbors = this.adjacencyList.get(nodeId) || new Set();
    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        this.topologicalSortUtil(neighborId, visited, stack);
      }
    }

    stack.push(nodeId);
  }

  getUpstreamNodes(nodeId: string): DataNode[] {
    const sourceIds = this.reverseAdjacencyList.get(nodeId) || new Set();
    return Array.from(sourceIds)
      .map((id) => this.nodeIndex.get(id)!)
      .filter(Boolean);
  }

  getDownstreamNodes(nodeId: string): DataNode[] {
    const targetIds = this.adjacencyList.get(nodeId) || new Set();
    return Array.from(targetIds)
      .map((id) => this.nodeIndex.get(id)!)
      .filter(Boolean);
  }

  getSourceNodes(): DataNode[] {
    return this.getAllNodes().filter(
      (node) => (this.reverseAdjacencyList.get(node.id)?.size || 0) === 0,
    );
  }

  getSinkNodes(): DataNode[] {
    return this.getAllNodes().filter(
      (node) => (this.adjacencyList.get(node.id)?.size || 0) === 0,
    );
  }

  // Business validation using DataNode logic
  validateConnection(sourceId: string, targetId: string): boolean {
    const source = this.nodeIndex.get(sourceId);
    const target = this.nodeIndex.get(targetId);
    return source?.canConnectWith(target) || false;
  }

  detectCycles(): string[][] {
    const cycles: string[][] = [];
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    for (const nodeId of this.nodeIndex.keys()) {
      if (!visited.has(nodeId)) {
        this.detectCyclesUtil(nodeId, visited, recursionStack, [], cycles);
      }
    }

    return cycles;
  }

  private detectCyclesUtil(
    nodeId: string,
    visited: Set<string>,
    recursionStack: Set<string>,
    currentPath: string[],
    cycles: string[][],
  ): void {
    visited.add(nodeId);
    recursionStack.add(nodeId);
    currentPath.push(nodeId);

    const neighbors = this.adjacencyList.get(nodeId) || new Set();
    for (const neighborId of neighbors) {
      if (recursionStack.has(neighborId)) {
        // Found cycle
        const cycleStart = currentPath.indexOf(neighborId);
        cycles.push([...currentPath.slice(cycleStart), neighborId]);
      } else if (!visited.has(neighborId)) {
        this.detectCyclesUtil(
          neighborId,
          visited,
          recursionStack,
          currentPath,
          cycles,
        );
      }
    }

    recursionStack.delete(nodeId);
    currentPath.pop();
  }

  isAcyclic(): boolean {
    return this.detectCycles().length === 0;
  }

  // Query nodes by business identity
  getNodesByPointId(pointId: string): DataNode[] {
    return this.getAllNodes().filter((node) => node.pointId === pointId);
  }

  // React Flow integration - clean separation of concerns
  toReactFlow(): { nodes: Node[]; edges: Edge[] } {
    const nodes = this.getAllNodes().map((dataNode) => ({
      id: dataNode.id,
      type: dataNode.type,
      position: (dataNode as any).position || { x: 0, y: 0 },
      data: dataNode, // DataNode object becomes React Flow node data
    }));

    const edges = this.getAllEdges().map((edge) => ({
      id: `${edge.source.id}-to-${edge.target.id}`,
      source: edge.source.id,
      target: edge.target.id,
    }));

    return { nodes, edges };
  }

  fromReactFlow(nodes: Node[], edges: Edge[]): void {
    // Clear existing graph
    this.nodeIndex.clear();
    this.adjacencyList.clear();
    this.reverseAdjacencyList.clear();

    // Add nodes (assuming node.data contains DataNode objects)
    nodes.forEach((node) => {
      const dataNode = node.data as DataNode;
      this.addNode(dataNode);
    });

    // Add connections
    edges.forEach((edge) => {
      this.addConnection(edge.source, edge.target);
    });
  }
}
```

### 4.5 FlowValidator Class Specification

```typescript
export class FlowValidator {
  private graph: FlowGraph;
  private errors: ValidationError[];

  constructor(graph: FlowGraph) {
    this.graph = graph;
    this.errors = [];
  }

  validate(): ValidationResult {
    this.errors = [];

    // Run all validation checks
    this.validateNodeTypes();
    this.validateConnections();
    this.validateCompleteness();
    this.validateCycles();
    this.validateDataFlow();

    return {
      isValid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.getWarnings(),
    };
  }

  private validateNodeTypes(): void;
  private validateConnections(): void {
    // Validate all connections using DataNode business logic
    const edges = this.graph.getAllEdges();
    for (const edge of edges) {
      if (!edge.source.canConnectWith(edge.target)) {
        this.errors.push({
          type: "invalid_connection",
          message: `Invalid connection: ${edge.source.type} cannot connect to ${edge.target.type}`,
          sourceId: edge.source.id,
          targetId: edge.target.id,
        });
      }
    }
  }

  private validateCompleteness(): void {
    // Check for nodes that require inputs but have none
    const nodes = this.graph.getAllNodes();
    for (const node of nodes) {
      if (
        node.direction === NodeDirection.INPUT ||
        node.direction === NodeDirection.BIDIRECTIONAL
      ) {
        const upstreamNodes = this.graph.getUpstreamNodes(node.id);
        if (upstreamNodes.length === 0 && node.type !== "analog-input") {
          this.errors.push({
            type: "missing_inputs",
            message: `Node ${node.type} requires input connections`,
            nodeId: node.id,
          });
        }
      }
    }
  }

  private validateCycles(): void {
    const cycles = this.graph.detectCycles();
    for (const cycle of cycles) {
      this.errors.push({
        type: "cycle_detected",
        message: `Cycle detected in control flow: ${cycle.join(" → ")}`,
        nodeIds: cycle,
      });
    }
  }

  private validateDataFlow(): void {
    // Ensure all DataNode objects have proper business validation
    const nodes = this.graph.getAllNodes();
    for (const node of nodes) {
      if (!node.id || !node.pointId || !node.type) {
        this.errors.push({
          type: "invalid_node_data",
          message: `Node missing required properties (id, pointId, type)`,
          nodeId: node.id || "unknown",
        });
      }
    }
  }

  private getWarnings(): ValidationWarning[] {
    const warnings: ValidationWarning[] = [];

    // Check for orphan nodes
    const orphans = this.findOrphanNodes();
    if (orphans.length > 0) {
      warnings.push({
        type: "orphan_nodes",
        message: `Found ${orphans.length} disconnected nodes`,
        nodeIds: orphans,
      });
    }

    // Check for dead ends
    const deadEnds = this.findDeadEnds();
    if (deadEnds.length > 0) {
      warnings.push({
        type: "dead_ends",
        message: `Found ${deadEnds.length} nodes with no output`,
        nodeIds: deadEnds,
      });
    }

    return warnings;
  }

  private findOrphanNodes(): string[];
  private findDeadEnds(): string[];
}
```

### 4.6 FlowExecutor Class Specification

```typescript
export class FlowExecutor {
  private graph: FlowGraph;
  private executionOrder: string[];

  constructor(graph: FlowGraph) {
    this.graph = graph;
    this.executionOrder = [];
  }

  prepare(): ExecutionPlan {
    const order = this.graph.getExecutionOrder();

    if (!order) {
      throw new Error("Cannot execute flow with cycles");
    }

    this.executionOrder = order;

    return {
      order: this.executionOrder,
      stages: this.groupIntoStages(),
      estimatedDuration: this.estimateDuration(),
    };
  }

  // Group nodes that can execute in parallel
  private groupIntoStages(): string[][] {
    const levels: string[][] = [];
    const visited = new Set<string>();
    const inDegree = new Map<string, number>();

    // Calculate in-degrees
    for (const nodeId of this.graph.getAllNodes().map((n) => n.id)) {
      inDegree.set(nodeId, this.graph.getNodeDegree(nodeId).inDegree);
    }

    while (visited.size < this.graph.getAllNodes().length) {
      // Find all nodes with no unprocessed dependencies
      const currentLevel: string[] = [];

      for (const [nodeId, degree] of inDegree.entries()) {
        if (!visited.has(nodeId) && degree === 0) {
          currentLevel.push(nodeId);
        }
      }

      if (currentLevel.length === 0) {
        throw new Error("Circular dependency detected in execution stages");
      }

      levels.push(currentLevel);

      // Mark nodes as visited and update in-degrees
      for (const nodeId of currentLevel) {
        visited.add(nodeId);

        // Reduce in-degree for all downstream nodes
        const downstream = this.graph.getDownstreamNodes(nodeId);
        for (const downstreamId of downstream) {
          const currentDegree = inDegree.get(downstreamId) || 0;
          inDegree.set(downstreamId, Math.max(0, currentDegree - 1));
        }
      }
    }

    return levels;
  }

  // Estimate execution time based on node types (in milliseconds)
  private estimateDuration(): number {
    const NODE_DURATIONS = {
      "bacnet.ai": 50, // BACnet read operation
      "bacnet.ao": 50, // BACnet read operation
      "bacnet.bi": 30, // Binary read (faster)
      "bacnet.bo": 30, // Binary read (faster)
      "bacnet.av": 40, // Analog value read
      "bacnet.bv": 25, // Binary value read
      "logic.compare": 5, // Simple comparison
      "logic.calculate": 10, // Mathematical operation
      "logic.condition": 8, // Conditional logic
      "logic.timer": 15, // Timer operations
      "logic.schedule": 20, // Schedule evaluation
      "command.setValue": 100, // BACnet write operation
    };

    let totalDuration = 0;
    const stages = this.groupIntoStages();

    // Stages execute in sequence, nodes within a stage execute in parallel
    for (const stage of stages) {
      let maxStageTime = 0;

      for (const nodeId of stage) {
        const node = this.graph.getNode(nodeId);
        if (node) {
          const nodeDuration =
            NODE_DURATIONS[node.data.nodeType as keyof typeof NODE_DURATIONS] ||
            50;
          maxStageTime = Math.max(maxStageTime, nodeDuration);
        }
      }

      totalDuration += maxStageTime;
    }

    // Add 20% overhead for system processing
    return Math.round(totalDuration * 1.2);
  }

  // Simulate data flow through the graph
  simulateDataFlow(inputs: Map<string, any>): SimulationResult {
    const nodeOutputs = new Map<string, any>();
    const errors: string[] = [];
    const startTime = performance.now();

    try {
      for (const nodeId of this.executionOrder) {
        const node = this.graph.getNode(nodeId);
        if (!node) {
          errors.push(`Node ${nodeId} not found`);
          continue;
        }

        try {
          const inputData = this.gatherNodeInputs(nodeId, nodeOutputs);
          const output = this.simulateNode(node, inputData);
          nodeOutputs.set(nodeId, output);
        } catch (error) {
          const errorMsg = `Node ${nodeId}: ${
            error instanceof Error ? error.message : "Unknown error"
          }`;
          errors.push(errorMsg);
        }
      }

      const executionTime = performance.now() - startTime;

      return {
        success: errors.length === 0,
        outputs: nodeOutputs,
        executionPath: this.executionOrder,
        errors: errors.length > 0 ? errors : undefined,
        executionTime,
        stages: this.groupIntoStages(),
        estimatedDuration: this.estimateDuration(),
      };
    } catch (error) {
      return {
        success: false,
        outputs: new Map(),
        executionPath: [],
        errors: [
          `Simulation failed: ${
            error instanceof Error ? error.message : "Unknown error"
          }`,
        ],
        executionTime: performance.now() - startTime,
      };
    }
  }

  private gatherNodeInputs(
    nodeId: string,
    outputs: Map<string, any>,
  ): Record<string, any> {
    const inputs: Record<string, any> = {};

    // Get all upstream nodes that feed into this node
    const upstreamNodes = this.graph.getUpstreamNodes(nodeId);

    for (const upstreamId of upstreamNodes) {
      const upstreamOutput = outputs.get(upstreamId);
      if (upstreamOutput !== undefined) {
        inputs[upstreamId] = upstreamOutput;
      }
    }

    return inputs;
  }

  private simulateNode(node: FlowNode, inputs: Record<string, any>): any {
    const nodeType = node.data.nodeType;

    switch (nodeType) {
      case "bacnet.ai":
      case "bacnet.ao":
      case "bacnet.av":
        // Simulate analog values
        return {
          presentValue: 72.5 + Math.random() * 5, // Simulate temperature reading
          units: "°F",
          reliability: "no-fault-detected",
          timestamp: new Date().toISOString(),
        };

      case "bacnet.bi":
      case "bacnet.bo":
      case "bacnet.bv":
        // Simulate binary values
        return {
          presentValue: Math.random() > 0.5,
          reliability: "no-fault-detected",
          timestamp: new Date().toISOString(),
        };

      case "logic.compare":
        // Simulate comparison logic
        const inputValues = Object.values(inputs).map(
          (i) => i?.presentValue || 0,
        );
        if (inputValues.length >= 2) {
          return {
            result: inputValues[0] > inputValues[1],
            operation: "greater_than",
            inputs: inputValues,
            timestamp: new Date().toISOString(),
          };
        }
        return { result: false, error: "Insufficient inputs" };

      case "logic.calculate":
        // Simulate mathematical operations
        const calcInputs = Object.values(inputs).map(
          (i) => i?.presentValue || 0,
        );
        const sum = calcInputs.reduce((a, b) => a + b, 0);
        return {
          result: sum,
          operation: "sum",
          inputs: calcInputs,
          timestamp: new Date().toISOString(),
        };

      case "logic.condition":
        // Simulate conditional logic
        const conditionInput = Object.values(inputs)[0];
        const isTrue =
          conditionInput?.result || conditionInput?.presentValue || false;
        return {
          result: isTrue ? "condition_met" : "condition_not_met",
          condition: isTrue,
          timestamp: new Date().toISOString(),
        };

      case "logic.timer":
        // Simulate timer
        return {
          elapsed: Math.random() * 1000,
          active: true,
          timestamp: new Date().toISOString(),
        };

      case "logic.schedule":
        // Simulate schedule evaluation
        const currentHour = new Date().getHours();
        return {
          active: currentHour >= 8 && currentHour <= 18, // Business hours
          nextTransition: "18:00",
          timestamp: new Date().toISOString(),
        };

      case "command.setValue":
        // Simulate set value command
        const setValue = Object.values(inputs)[0]?.result || 0;
        return {
          command: "writeProperty",
          value: setValue,
          status: "success",
          timestamp: new Date().toISOString(),
        };

      default:
        throw new Error(`Unknown node type: ${nodeType}`);
    }
  }
}
```

### 4.7 Flow Slice Specification

The Flow slice acts as the bridge between the Infrastructure Management UI (tree view) and the Execution Graph (canvas). It handles the transformation of discovered BACnet points into executable DataNode instances on the canvas.

```typescript
// Flow Slice - Bridge between Infrastructure and Execution
interface FlowSlice {
  // Canvas nodes and edges
  nodes: Node[]; // React Flow nodes
  edges: Edge[]; // React Flow edges

  // DataGraph instance for execution logic
  dataGraph: DataGraph; // Business logic graph

  // Actions
  addNodeFromInfrastructure: (
    draggedPoint: DraggedPoint,
    position: XYPosition,
  ) => void;
  removeNode: (nodeId: string) => void;
  updateNodePosition: (nodeId: string, position: XYPosition) => void;

  connectNodes: (connection: Connection) => boolean;
  disconnectNodes: (edgeId: string) => void;

  validateFlow: () => ValidationResult;
  getExecutionOrder: () => string[];
  exportToSchema: () => FlowConfiguration;
  importFromSchema: (config: FlowConfiguration) => void;

  // Selection management
  selectedNodes: string[];
  selectNode: (nodeId: string, multi?: boolean) => void;
  clearSelection: () => void;

  // Undo/Redo
  history: FlowState[];
  historyIndex: number;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}

// Drag data from Infrastructure to Canvas
interface DraggedPoint {
  type: "bacnet-point";

  // Infrastructure identifiers
  supervisorId: string;
  controllerId: string;
  ipAddress: string;

  // BACnet point data
  objectType: "AI" | "AO" | "AV" | "BI" | "BO" | "BV";
  objectId: number;
  objectName: string;
  presentValue: number | boolean;
  units?: string;
  description?: string;

  // UI metadata
  draggedFrom: "controllers-tree";
}

// Flow slice implementation
export const createFlowSlice: StateCreator<AppState, [], [], FlowSlice> = (
  set,
  get,
) => ({
  // Initial state
  nodes: [],
  edges: [],
  dataGraph: new DataGraph(),
  selectedNodes: [],
  history: [],
  historyIndex: -1,
  canUndo: false,
  canRedo: false,

  // Transform infrastructure point to canvas node
  addNodeFromInfrastructure: (
    draggedPoint: DraggedPoint,
    position: XYPosition,
  ) => {
    const state = get();

    // Create BACnet configuration from dragged point
    const bacnetConfig: BacnetConfig = {
      objectId: draggedPoint.objectId,
      supervisorId: draggedPoint.supervisorId,
      controllerId: draggedPoint.controllerId,
      presentValue: draggedPoint.presentValue,
      units: draggedPoint.units,
      description:
        draggedPoint.description ||
        `${draggedPoint.objectType}-${draggedPoint.objectId}`,
      reliability: "no-fault-detected",
      statusFlags: {
        inAlarm: false,
        fault: false,
        overridden: false,
        outOfService: false,
      },
      label: draggedPoint.objectName,
      position,
    };

    // Create DataNode instance based on object type
    let dataNode: DataNode;
    switch (draggedPoint.objectType) {
      case "AI":
        dataNode = new AnalogInputNode(bacnetConfig);
        break;
      case "AO":
        dataNode = new AnalogOutputNode(bacnetConfig);
        break;
      case "AV":
        dataNode = new AnalogValueNode(bacnetConfig);
        break;
      case "BI":
        dataNode = new BinaryInputNode(bacnetConfig);
        break;
      case "BO":
        dataNode = new BinaryOutputNode(bacnetConfig);
        break;
      case "BV":
        dataNode = new BinaryValueNode(bacnetConfig);
        break;
      default:
        throw new Error(`Unknown object type: ${draggedPoint.objectType}`);
    }

    // Add to DataGraph (business logic)
    state.dataGraph.addNode(dataNode);

    // Create React Flow node (UI representation)
    const reactFlowNode: Node = {
      id: dataNode.id,
      type: `bacnet.${draggedPoint.objectType.toLowerCase()}`,
      position,
      data: dataNode, // DataNode IS the data
      selected: false,
      dragging: false,
    };

    // Update state with new node
    set((state) => ({
      nodes: [...state.nodes, reactFlowNode],
      selectedNodes: [dataNode.id], // Auto-select new node
    }));

    // Record history for undo/redo
    get().recordHistory();
  },

  removeNode: (nodeId: string) => {
    const state = get();

    // Remove from DataGraph
    state.dataGraph.removeNode(nodeId);

    // Remove from React Flow
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== nodeId),
      edges: state.edges.filter(
        (e) => e.source !== nodeId && e.target !== nodeId,
      ),
      selectedNodes: state.selectedNodes.filter((id) => id !== nodeId),
    }));

    get().recordHistory();
  },

  updateNodePosition: (nodeId: string, position: XYPosition) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId ? { ...node, position } : node,
      ),
    }));
  },

  connectNodes: (connection: Connection) => {
    const state = get();

    // Validate connection using DataGraph business logic
    if (
      !state.dataGraph.validateConnection(
        connection.source!,
        connection.target!,
      )
    ) {
      console.warn("Invalid connection attempt");
      return false;
    }

    // Add to DataGraph
    const added = state.dataGraph.addConnection(
      connection.source!,
      connection.target!,
    );

    if (added) {
      // Create React Flow edge
      const newEdge: Edge = {
        id: `${connection.source}-to-${connection.target}`,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle || undefined,
        targetHandle: connection.targetHandle || undefined,
        type: "smoothstep",
        animated: false,
        style: { stroke: "#64748b", strokeWidth: 2 },
      };

      set((state) => ({
        edges: [...state.edges, newEdge],
      }));

      get().recordHistory();
      return true;
    }

    return false;
  },

  disconnectNodes: (edgeId: string) => {
    const state = get();
    const edge = state.edges.find((e) => e.id === edgeId);

    if (edge) {
      // Remove from DataGraph
      state.dataGraph.removeConnection(edge.source, edge.target);

      // Remove from React Flow
      set((state) => ({
        edges: state.edges.filter((e) => e.id !== edgeId),
      }));

      get().recordHistory();
    }
  },

  validateFlow: () => {
    const state = get();
    const validator = new FlowValidator(state.dataGraph);
    return validator.validate();
  },

  getExecutionOrder: () => {
    const state = get();
    return state.dataGraph.getExecutionOrder();
  },

  exportToSchema: () => {
    const state = get();

    // Convert DataGraph to schema format for IoT Supervisor
    const nodes = state.dataGraph.getAllNodes();
    const edges = state.dataGraph.getAllEdges();

    return {
      version: "1.0.0",
      nodes: nodes.map((node) => ({
        id: node.id,
        pointId: node.pointId,
        type: node.type,
        config: node as BacnetConfig, // Full configuration
      })),
      edges: edges.map((edge) => ({
        source: edge.source.id,
        target: edge.target.id,
      })),
      metadata: {
        createdAt: new Date().toISOString(),
        projectId: get().projectId,
      },
    };
  },

  importFromSchema: (config: FlowConfiguration) => {
    // Clear current flow
    set({ nodes: [], edges: [], selectedNodes: [] });

    const dataGraph = new DataGraph();
    const reactFlowNodes: Node[] = [];
    const reactFlowEdges: Edge[] = [];

    // Recreate nodes
    for (const nodeConfig of config.nodes) {
      // Create DataNode from config
      const dataNode = createDataNodeFromConfig(nodeConfig);
      dataGraph.addNode(dataNode);

      // Create React Flow node
      reactFlowNodes.push({
        id: dataNode.id,
        type: getReactFlowType(dataNode.type),
        position: nodeConfig.config.position || { x: 0, y: 0 },
        data: dataNode,
      });
    }

    // Recreate edges
    for (const edgeConfig of config.edges) {
      if (dataGraph.addConnection(edgeConfig.source, edgeConfig.target)) {
        reactFlowEdges.push({
          id: `${edgeConfig.source}-to-${edgeConfig.target}`,
          source: edgeConfig.source,
          target: edgeConfig.target,
          type: "smoothstep",
        });
      }
    }

    set({
      nodes: reactFlowNodes,
      edges: reactFlowEdges,
      dataGraph,
    });
  },

  selectNode: (nodeId: string, multi = false) => {
    set((state) => ({
      selectedNodes: multi
        ? state.selectedNodes.includes(nodeId)
          ? state.selectedNodes.filter((id) => id !== nodeId)
          : [...state.selectedNodes, nodeId]
        : [nodeId],
    }));
  },

  clearSelection: () => {
    set({ selectedNodes: [] });
  },

  // History management for undo/redo
  recordHistory: () => {
    const state = get();
    const snapshot = {
      nodes: [...state.nodes],
      edges: [...state.edges],
      dataGraph: state.dataGraph.clone(), // Assumes clone method exists
    };

    set((state) => {
      const newHistory = state.history.slice(0, state.historyIndex + 1);
      newHistory.push(snapshot);

      return {
        history: newHistory.slice(-50), // Keep last 50 states
        historyIndex: newHistory.length - 1,
        canUndo: newHistory.length > 1,
        canRedo: false,
      };
    });
  },

  undo: () => {
    const state = get();
    if (state.historyIndex > 0) {
      const previousState = state.history[state.historyIndex - 1];
      set({
        nodes: previousState.nodes,
        edges: previousState.edges,
        dataGraph: previousState.dataGraph,
        historyIndex: state.historyIndex - 1,
        canUndo: state.historyIndex - 1 > 0,
        canRedo: true,
      });
    }
  },

  redo: () => {
    const state = get();
    if (state.historyIndex < state.history.length - 1) {
      const nextState = state.history[state.historyIndex + 1];
      set({
        nodes: nextState.nodes,
        edges: nextState.edges,
        dataGraph: nextState.dataGraph,
        historyIndex: state.historyIndex + 1,
        canUndo: true,
        canRedo: state.historyIndex + 1 < state.history.length - 1,
      });
    }
  },
});

// Helper functions
function getReactFlowType(dataNodeType: string): string {
  // Map DataNode types to React Flow node types
  const typeMap: Record<string, string> = {
    "analog-input": "bacnet.ai",
    "analog-output": "bacnet.ao",
    "analog-value": "bacnet.av",
    "binary-input": "bacnet.bi",
    "binary-output": "bacnet.bo",
    "binary-value": "bacnet.bv",
    comparison: "logic.compare",
    calculation: "logic.calculate",
    condition: "logic.condition",
    timer: "logic.timer",
    schedule: "logic.schedule",
    "write-setpoint": "command.setValue",
  };
  return typeMap[dataNodeType] || dataNodeType;
}

function createDataNodeFromConfig(nodeConfig: any): DataNode {
  // Factory method to recreate DataNode from saved configuration
  const { type, config } = nodeConfig;

  switch (type) {
    case "analog-input":
      return new AnalogInputNode(config);
    case "analog-output":
      return new AnalogOutputNode(config);
    case "analog-value":
      return new AnalogValueNode(config);
    // ... other node types
    default:
      throw new Error(`Unknown node type: ${type}`);
  }
}
```

**Flow Slice Integration Points**:

1. **With Infrastructure Slice**: Receives drag events and point data
2. **With DataGraph**: Manages business logic and validation
3. **With React Flow**: Synchronizes UI state with business state
4. **With Persistence**: Exports/imports configurations

**Benefits of Flow Slice Architecture**:

- 🎯 **Clear Separation**: Infrastructure (tree) vs Execution (canvas)
- 🔄 **Bidirectional Sync**: DataGraph ↔ React Flow state
- 🛡️ **Business Validation**: All connections validated by DataNode logic
- 📊 **Single Source of Truth**: DataGraph for execution, React Flow for UI
- 🔧 **Testable**: Business logic separate from UI concerns

## 5. UI-First Implementation Plan

> **Philosophy**: Build the visual interface first to get immediate feedback, then add sophisticated data modeling to support the proven UI patterns.

### Implementation Phases Overview

- **Phase 1**: Application Shell & BMS Infrastructure UI (Steps 1-6)
- **Phase 2**: BMS Infrastructure Management (Steps 7-9)
- **Phase 3**: Visual Programming Canvas (Steps 10-12)
- **Phase 4**: Canvas Controls & Node Management (Steps 13-14)
- **Phase 5**: Data Integration (Steps 15-17)
- **Phase 6**: Persistence & Integration (Steps 18-19)

---

## Phase 1: Application Shell & BMS Infrastructure UI

### Step 1: Install Dependencies

**Action**: Install React Flow and required dependencies

**Commands**:

```bash
cd apps/designer
pnpm add @xyflow/react zustand
```

**Expected Output**:

```
+ @xyflow/react 12.x.x
+ zustand 5.x.x
```

**Validation**:

- Dependencies appear in package.json
- No install errors or version conflicts

---

### Step 2: Main Layout Structure

**Action**: Create the main application layout with left sidebar and canvas area

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/layout/main-layout.tsx`

**UI Structure**:

```
┌─────────────────────────────────────────┐
│ Header (Project name, actions)          │
├──────────┬──────────────────────────────┤
│          │                              │
│  Left    │        Main Canvas           │
│ Sidebar  │     (React Flow)             │
│ (Tabs)   │                              │
│          │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

**Key Features**:

- Fixed left sidebar (300px width)
- Resizable splitter between sidebar and canvas
- Header with project context
- Responsive design for different screen sizes

---

### Step 3: Left Sidebar Tab Interface

**Action**: Create two-tab interface for BMS infrastructure management

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/sidebar/infrastructure-sidebar.tsx`

**Tab Structure**:

- **Tab 1: Controllers** - Manage controller IP addresses and point discovery
- **Tab 2: Supervisors** - Manage supervisor configurations

**UI Components**:

- Tab navigation (Controllers/Supervisors)
- Tab content panels with proper spacing
- Loading states and error handling
- Empty states with helpful messaging

---

### Step 4: Controllers Tab - Default Supervisor & IP Management

**Action**: Implement the Controllers tab with IP address management

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/sidebar/controllers-tab.tsx`

**Features**:

- Display default supervisor (non-editable)
- Add controller IP address form
- List of added controllers with remove buttons
- "Discover Points" action button per controller
- IP address validation
- Connection status indicators

**Mock Data Structure**:

```typescript
interface Controller {
  id: string;
  ipAddress: string;
  name?: string;
  status: "connected" | "disconnected" | "discovering";
  lastDiscovered?: Date;
  pointCount?: number;
}
```

---

### Step 5: Supervisors Tab - Configuration Management

**Action**: Implement the Supervisors tab for supervisor management

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/sidebar/supervisors-tab.tsx`

**Features**:

- List of available supervisors
- Add new supervisor form
- Edit supervisor settings
- Supervisor connection status
- Configuration validation

**Mock Data Structure**:

```typescript
interface Supervisor {
  id: string;
  name: string;
  ipAddress?: string;
  status: "active" | "inactive" | "error";
  controllerCount: number;
  description?: string;
}
```

---

### Step 6: Basic React Flow Canvas Setup

**Action**: Set up empty React Flow canvas in main area

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/canvas/flow-canvas.tsx`

**Features**:

- Empty React Flow instance
- Zoom and pan controls
- Background grid/dots
- Canvas bounds and limits
- Basic styling and theme

**Commands**:

```bash
pnpm test # Should pass basic component render tests
```

**Validation**:

- Canvas renders without errors
- Zoom/pan controls work
- Canvas fills available space
- No console errors

---

## Phase 2: BMS Infrastructure Management

### Step 7: Controller Discovery UI

**Action**: Implement IP address input form with "Discover Points" functionality

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/sidebar/controller-discovery.tsx`

**Features**:

- IP address input with validation
- "Discover Points" button with loading state
- Progress indicator during discovery
- Error handling and retry logic
- Success feedback with point count

**Mock Discovery Process**:

```typescript
interface DiscoveryResult {
  controllerInfo: {
    deviceId: number;
    name: string;
    modelName: string;
    firmwareVersion: string;
  };
  points: BACnetPoint[];
}

interface BACnetPoint {
  objectType: "AI" | "AO" | "AV" | "BI" | "BO" | "BV";
  instanceNumber: number;
  objectName: string;
  presentValue: any;
  units?: string;
  description?: string;
}
```

**UI States**:

- Idle: Show input form and discover button
- Discovering: Show progress spinner and cancel option
- Success: Show discovered points count and success message
- Error: Show error message and retry button

---

### Step 8: Points Tree View

**Action**: Display discovered BACnet points in hierarchical tree structure

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/sidebar/points-tree.tsx`

**Tree Structure**:

```
📁 Controller 192.168.1.100
├── 📁 Analog Inputs (AI)
│   ├── 🌡️ Temperature Sensor (AI-1)
│   ├── 🌡️ Humidity Sensor (AI-2)
│   └── 📊 Pressure Sensor (AI-3)
├── 📁 Analog Outputs (AO)
│   ├── 🔧 Valve Control (AO-1)
│   └── 🔧 Damper Control (AO-2)
└── 📁 Analog Values (AV)
    ├── 🎯 Setpoint Temperature (AV-1)
    └── 🎯 Setpoint Humidity (AV-2)
```

**Features**:

- Collapsible tree nodes by object type
- Icons for different BACnet object types
- Point details on hover (present value, units, description)
- Search/filter points by name
- Drag handles for canvas integration (Phase 3)

---

### Step 9: Drag from Infrastructure with Flow Slice Integration

**Action**: Enable dragging points from tree to canvas with Flow slice handling the transformation

**Files**:

- `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/hooks/use-point-drag.tsx` - Drag handling
- `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/store/flow-slice.ts` - Flow slice creation
- `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/canvas/flow-canvas.tsx` - Drop zone integration

**Features**:

- HTML5 drag and drop API integration
- Drag preview showing point information
- Drag data payload with BACnet point details
- Visual feedback during drag operation
- Drop zone validation (canvas area)
- **Flow slice creation for state management**
- **Transform infrastructure points to DataNode instances**

**Implementation Steps**:

1. **Create Flow Slice** (`src/store/flow-slice.ts`):

```typescript
import { StateCreator } from "zustand";
import { DataGraph } from "@/lib/flow-graph/DataGraph";
import { Node, Edge, Connection, XYPosition } from "@xyflow/react";

export interface FlowSlice {
  // Canvas state
  nodes: Node[];
  edges: Edge[];
  dataGraph: DataGraph;

  // Actions
  addNodeFromInfrastructure: (
    draggedPoint: DraggedPoint,
    position: XYPosition,
  ) => void;
  connectNodes: (connection: Connection) => boolean;
  validateFlow: () => ValidationResult;

  // Selection
  selectedNodes: string[];
  selectNode: (nodeId: string, multi?: boolean) => void;
}

export const createFlowSlice: StateCreator<AppState, [], [], FlowSlice> = (
  set,
  get,
) => ({
  nodes: [],
  edges: [],
  dataGraph: new DataGraph(),
  selectedNodes: [],

  addNodeFromInfrastructure: (draggedPoint, position) => {
    // Transform infrastructure point to DataNode
    const dataNode = createDataNodeFromPoint(draggedPoint);

    // Add to business logic graph
    get().dataGraph.addNode(dataNode);

    // Create React Flow node
    const reactFlowNode = {
      id: dataNode.id,
      type: `bacnet.${draggedPoint.objectType.toLowerCase()}`,
      position,
      data: dataNode,
    };

    // Update UI state
    set((state) => ({
      nodes: [...state.nodes, reactFlowNode],
      selectedNodes: [dataNode.id],
    }));
  },

  connectNodes: (connection) => {
    const { dataGraph } = get();

    // Validate using business logic
    if (!dataGraph.validateConnection(connection.source!, connection.target!)) {
      return false;
    }

    // Add to graph
    dataGraph.addConnection(connection.source!, connection.target!);

    // Update UI
    const edge = {
      id: `${connection.source}-to-${connection.target}`,
      ...connection,
    };

    set((state) => ({
      edges: [...state.edges, edge],
    }));

    return true;
  },
});
```

2. **Create Drag Hook** (`src/hooks/use-point-drag.tsx`):

```typescript
export function usePointDrag() {
  const addNodeFromInfrastructure = useFlowStore(
    (state) => state.addNodeFromInfrastructure,
  );

  const handleDragStart = useCallback(
    (e: DragEvent, point: BACnetPoint, controller: Controller) => {
      const draggedPoint: DraggedPoint = {
        type: "bacnet-point",
        supervisorId: controller.supervisorId,
        controllerId: controller.id,
        ipAddress: controller.ipAddress,
        objectType: point.objectType,
        objectId: point.instanceNumber,
        objectName: point.objectName,
        presentValue: point.presentValue,
        units: point.units,
        description: point.description,
        draggedFrom: "controllers-tree",
      };

      e.dataTransfer!.setData(
        "application/reactflow",
        JSON.stringify(draggedPoint),
      );
      e.dataTransfer!.effectAllowed = "copy";

      // Add drag preview
      const preview = createDragPreview(point);
      e.dataTransfer!.setDragImage(preview, 0, 0);
    },
    [],
  );

  return { handleDragStart };
}
```

3. **Update Canvas Drop Zone** (`src/components/canvas/flow-canvas.tsx`):

```typescript
export function FlowCanvas() {
  const { nodes, edges, addNodeFromInfrastructure } = useFlowStore()
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance>()

  const onDrop = useCallback((event: DragEvent) => {
    event.preventDefault()

    const reactFlowBounds = reactFlowWrapper.current!.getBoundingClientRect()
    const data = event.dataTransfer!.getData('application/reactflow')

    if (data) {
      const draggedPoint: DraggedPoint = JSON.parse(data)

      // Calculate drop position in flow coordinates
      const position = reactFlowInstance!.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      })

      // Use Flow slice to add node
      addNodeFromInfrastructure(draggedPoint, position)
    }
  }, [reactFlowInstance, addNodeFromInfrastructure])

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault()
    event.dataTransfer!.dropEffect = 'copy'
  }, [])

  return (
    <div ref={reactFlowWrapper} className="w-full h-full" onDrop={onDrop} onDragOver={onDragOver}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onInit={setReactFlowInstance}
        // ... other props
      />
    </div>
  )
}
```

**Drag Data Structure** (aligned with Flow slice):

```typescript
interface DraggedPoint {
  type: "bacnet-point";

  // Infrastructure identifiers
  supervisorId: string;
  controllerId: string;
  ipAddress: string;

  // BACnet point data
  objectType: "AI" | "AO" | "AV" | "BI" | "BO" | "BV";
  objectId: number;
  objectName: string;
  presentValue: number | boolean;
  units?: string;
  description?: string;

  // UI metadata
  draggedFrom: "controllers-tree";
}
```

**Integration Benefits**:

- 🎯 **Flow Slice Bridge**: Transforms infrastructure data to execution nodes
- 🔄 **Clean Data Flow**: Infrastructure → DraggedPoint → DataNode → React Flow Node
- 🛡️ **Business Validation**: All nodes validated through DataGraph
- 📊 **State Management**: Zustand manages both UI and business state
- 🔧 **Testable**: Each layer can be tested independently

---

## Phase 3: Visual Programming Canvas

### Step 10: BACnet Node Components

**Action**: Create visual node components for dragged BACnet points

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/nodes/bacnet-node.tsx`

**Features**:

- Different visual styles for AI, AO, AV, BI, BO, BV
- Node header with icon and object name
- Present value display
- Connection handles (input/output based on object type)
- Selected state styling
- Error/offline state indicators

**Node Visual Design**:

```
┌─────────────────────┐
│ 🌡️  Temperature     │ ← Header with icon
│ ○                  ◉│ ← Connection handles
│ 72.5°F             │ ← Present value
└─────────────────────┘
```

**Handle Configuration**:

- **AI/BI**: Output handle only (data source)
- **AO/BO**: Input handle only (data target)
- **AV/BV**: Bidirectional handles (data source and target)

---

### Step 11: Connection Handles

**Action**: Implement visual connection points with basic validation

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/nodes/connection-handle.tsx`

**Features**:

- Different handle styles for input/output/bidirectional
- Color coding by data type (analog/binary)
- Hover effects and tooltips
- Connection validation preview
- Handle positioning (left/right/both sides)

**Handle Types**:

- **Input Handle**: Blue circle, left side, receives data
- **Output Handle**: Green circle, right side, sends data
- **Bidirectional Handle**: Orange circle, both sides, sends/receives

---

### Step 12: Edge Creation

**Action**: Enable connecting nodes with temporary validation rules

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/hooks/use-connection-validation.tsx`

**Features**:

- Real-time connection validation during drag
- Visual feedback for valid/invalid connections
- Temporary connection rules (to be refined in Phase 5)
- Edge creation with proper styling
- Connection error messages

**Basic Validation Rules**:

- Output → Input connections only
- No self-connections
- Analog/Binary type compatibility
- Single input per target handle

---

## Phase 4: Canvas Controls & Node Management

### Step 13: Node Properties Panel

**Action**: Create properties panel for selected nodes

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/properties/node-properties-panel.tsx`

**Features**:

- Slide-in panel from right side
- Node-specific property forms
- Real-time value updates
- Validation and error display
- Save/cancel actions

**Property Categories**:

- **Basic Info**: Name, description, object ID
- **Current Value**: Present value, units, timestamp
- **Configuration**: Limits, defaults, overrides
- **Status**: Reliability, status flags, alarms

---

### Step 14: Canvas Toolbar

**Action**: Add toolbar with canvas and project controls

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/toolbar/canvas-toolbar.tsx`

**Toolbar Actions**:

- **Zoom**: Fit view, zoom in/out, zoom to selection
- **Selection**: Select all, select none, invert selection
- **Edit**: Delete selected, copy/paste, undo/redo
- **Project**: Save project, export configuration
- **Deploy**: Send to IoT supervisor (Phase 6)

**Layout**: Fixed toolbar at top of canvas area with icon buttons and tooltips

---

## Phase 5: Data Integration

### Step 15: DataNode System Implementation

**Action**: Implement business logic behind the working UI

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/lib/data-nodes/`

**Components**:

- DataNode interface and base classes
- BACnet-specific node implementations
- UUID utilities for deterministic IDs
- Connection validation logic
- Factory pattern for node creation

**Integration**: Connect existing UI components to DataNode instances without changing UI behavior

---

### Step 16: FlowGraph Implementation

**Action**: Add graph data structure to support canvas operations

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/lib/flow-graph/flow-graph.ts`

**Features**:

- Adjacency list with DataNode references
- Graph traversal and analysis methods
- Connection validation using node logic
- Export to schema format
- Import from saved configurations

**Integration**: FlowGraph manages data while React Flow manages UI presentation

---

### Step 17: Zustand Store Integration

**Action**: Connect UI state to data models

**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/store/flow-store.ts`

**Store Responsibilities**:

- Manage FlowGraph instance
- Sync with React Flow state
- Handle node/edge CRUD operations
- Provide undo/redo functionality
- Trigger UI updates

**Clean Separation**: Store bridges UI (React Flow) with business logic (DataNodes/FlowGraph)

---

## Phase 6: Persistence & Integration

### Step 18: Project + Infrastructure Persistence

**Action**: Save controller configs and flow designs to database

**Database Updates**:

```sql
-- Add infrastructure tables
CREATE TABLE controllers (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES projects(id),
  ip_address TEXT NOT NULL,
  name TEXT,
  device_id INTEGER,
  status TEXT DEFAULT 'disconnected',
  last_discovered TIMESTAMP,
  discovered_points TEXT, -- JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supervisors (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES projects(id),
  name TEXT NOT NULL,
  ip_address TEXT,
  status TEXT DEFAULT 'inactive',
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update projects table
ALTER TABLE projects ADD COLUMN infrastructure_config TEXT;
```

**Features**:

- Save/load controller configurations
- Persist discovered points
- Project templates with default infrastructure
- Export/import project configurations

---

### Step 19: IoT Supervisor Integration

**Action**: Send visual programs to execution engine

**API Integration**:

```typescript
// Convert FlowGraph to schema format
const configPayload = flowGraph.exportToSchema();

// Send to IoT supervisor
const response = await fetch("/api/deploy", {
  method: "POST",
  body: JSON.stringify({
    supervisorId,
    configuration: configPayload,
  }),
});
```

**Features**:

- Real-time deployment to supervisors
- Configuration validation before deployment
- Deployment status tracking
- Rollback to previous configurations
- Live monitoring of deployed flows

---

## Implementation Testing Strategy

### Per-Phase Testing

**Phase 1-2**: Component rendering, user interactions, mock data
**Phase 3**: Drag and drop, visual connections, canvas operations
**Phase 4**: Property editing, toolbar actions, UI state management
**Phase 5**: Data model integration, business logic validation
**Phase 6**: Database persistence, API integration, end-to-end workflows

### Test Commands

```bash
# Component tests
pnpm test

# Phase-specific tests
pnpm test:ui          # Phases 1-4 (UI components)
pnpm test:data        # Phase 5 (Data integration)
pnpm test:integration # Phase 6 (Full integration)

# Coverage and quality
pnpm test:coverage
pnpm lint
pnpm type-check
```

### Validation Criteria

**Each Phase Complete When**:

- All components render without errors
- User interactions work as expected
- Tests pass with good coverage
- No TypeScript errors
- Performance meets requirements
- UX feels smooth and responsive

This UI-first approach ensures we build a solid, usable interface before adding complex data modeling, leading to better user experience and faster development iterations.

---

## Phase 7: Supervisor Management (Deferred)

### Step 20: Supervisors Tab - Configuration Management

**Action**: Implement the Supervisors tab for supervisor management
**File**: `/Users/amol/Documents/ai-projects/bms-supervisor-controller/apps/designer/src/components/sidebar/supervisors-tab.tsx`

**Features**:

- List of available supervisors
- Add new supervisor form
- Edit supervisor settings
- Supervisor connection status
- Configuration validation
- Supervisor discovery and auto-detection
- Multi-supervisor coordination

**Mock Data Structure**:

```typescript
interface Supervisor {
  id: string;
  name: string;
  ipAddress?: string;
  status: "active" | "inactive" | "error";
  controllerCount: number;
  description?: string;
  lastSeen?: Date;
  capabilities?: string[];
}
```

**Implementation Details**:

- Support for multiple supervisors in different zones/buildings
- Supervisor hierarchy and grouping
- Automatic supervisor discovery via network scan
- Health monitoring and alerting
- Load balancing across supervisors
- Failover and redundancy configuration

**Rationale for Deferral**:

- Primary use case focuses on single default supervisor
- Controllers tab provides sufficient functionality for initial deployment
- Multi-supervisor scenarios are advanced use cases
- Allows focus on core visual programming features first

**Future Enhancements**:

- Supervisor clustering for high availability
- Cross-supervisor flow coordination
- Centralized supervisor management dashboard
- Historical supervisor performance metrics
