# BMS Supervisor Controller - Architecture Overview

**Created**: September 1, 2025
**Version**: 1.0
**Authors**: Development Team

## 1. Executive Summary

### 1.1 Purpose

The BMS Supervisor Controller is a visual programming tool designed specifically for BMS integrators to create, test, and deploy Building Management System control logic using visual flow-based programming. The tool generates Python code from visual flows, eliminating the need for manual programming while providing the flexibility and power that integrators need during system commissioning and configuration.

### 1.2 Key Stakeholders

- **BMS Integrators**: Primary users who design and deploy control logic during system commissioning
- **Controls Engineers**: Technical staff creating complex control strategies
- **System Installers**: Deploy and configure BMS systems at customer sites
- **Technical Support Teams**: Debug and optimize deployed control flows

Note: Production monitoring is handled by a separate application. This tool focuses on the development and deployment workflow.

### 1.3 Success Criteria

- BMS integrators can create control logic 5x faster than traditional programming
- Generated Python code matches hand-written code performance
- One-click deployment to IoT devices
- Each IoT device serves its own web dashboard at http://[device-ip]:8080
- Primary support for BACnet/IP with plugin architecture for other protocols

## 2. Functional Requirements

### 2.1 Visual Flow Creation

- **As a BMS integrator**, I want to drag and drop nodes to create control flows, so I can design logic without writing code
- **As a controls engineer**, I want to connect nodes with edges to define data flow, so I can visualize system relationships
- **As a BMS integrator**, I want to configure node properties through forms, so I can set parameters without syntax errors

### 2.2 BACnet Integration

- **As a BMS integrator**, I want to discover BACnet devices on the network, so I can see available equipment during design
- **As a controls engineer**, I want to browse device objects and properties, so I can select the correct data points
- **As a BMS integrator**, I want to see live values while editing flows, so I can verify device connectivity

### 2.3 Project Management

- **As a BMS integrator**, I want to save and load projects locally, so I can work on multiple sites
- **As a controls engineer**, I want to version my configurations, so I can track changes and rollback if needed
- **As a BMS integrator**, I want to export project files, so I can share configurations with team members

### 2.4 Deployment & BYOD Support

- **As a BMS integrator**, I want to deploy projects directly from Designer, so I can quickly configure remote IoT Supervisor devices
- **As a system installer**, I want to deploy BMS IoT Supervisor to any Linux device on-site, so I can use customer-provided hardware
- **As a BMS integrator**, I want to manage multiple IoT Supervisor devices from Designer, so I can configure multiple sites centrally
- **As a controls engineer**, I want to deploy both Designer and IoT Supervisor containers to Raspberry Pi/industrial PC, so I can use BYOD approach with full functionality
- **As a system installer**, I want one-click multi-container deployment, so I can commission systems quickly
- **As a technical support team**, I want over-the-air updates for both containers, so I can fix issues remotely
- **As a system installer**, I want deployment rollback capabilities, so I can recover from failed deployments

### 2.5 Development & Testing

- **As a controls engineer**, I want to test flows against simulated BACnet devices, so I can verify logic before deployment
- **As a BMS integrator**, I want to run the IoT app locally during development, so I can debug configurations

### 2.6 Production Monitoring

- **As a system installer**, I want to access device dashboards via web browser, so I can monitor deployed systems
- **As a building operator**, I want to view 15-minute historical data on any device, so I can track system performance
- **As a technical support team**, I want to check device status remotely, so I can provide support without site visits

## 3. System Architecture

### 3.1 High-Level Architecture

**Two-Application System**: The architecture consists of two focused applications for BMS control flow development and execution.

**Deployment**: Direct API-based deployment with manual Docker container management

### 3.2 Monorepo Structure

**PNPM Workspace Configuration**:

```
bms-supervisor-controller/
├── apps/
│   ├── designer/               # Next.js standalone app
│   │   ├── package.json        # App dependencies
│   │   ├── next.config.js      # Next.js configuration
│   │   └── ...                 # App source code
│   ├── runtime/               # FastAPI app (includes BACnet client)
│   │   ├── pyproject.toml     # Python dependencies
│   │   ├── main.py            # FastAPI entry point
│   │   └── ...                # App source code
│   └── simulator/             # BACnet simulator app
│       ├── pyproject.toml     # Python dependencies
│       ├── main.py            # Simulator entry point
│       └── ...                # Simulator source code
├── packages/
│   └── bms-schemas/          # Shared schema package
│       ├── package.json      # TypeScript tooling
│       ├── pyproject.toml    # Python tooling
│       ├── schemas.json      # Source of truth schemas
│       └── scripts/          # Code generation
├── package.json             # Root workspace config
├── pnpm-workspace.yaml      # PNPM workspace definition
└── .npmrc                   # PNPM configuration
```

**PNPM Workspace Benefits**:

- **Efficient storage**: Hard-linked dependencies across apps
- **Fast builds**: Parallel execution with workspace dependencies
- **Type safety**: TypeScript project references between packages
- **Unified tooling**: Single command to build all apps and packages

#### Development Mode (Both apps on integrator's laptop):

```
┌─────────────────────────────────────────────────────────────┐
│             BMS Designer (Next.js Standalone)              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Flow Editor │  │ Config Gen   │  │ Device Config    │  │
│  │ (React Flow)│  │ (Zod)        │  │ (IoT Supervisor IP)     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│                  Next.js (Port 3000)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SQLite: projects.db (flows, configs, projects)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Direct API Deployment
                          │ POST /api/config/deploy
                          ▼
┌─────────────────────────────────────────────────────────────┐
│   BMS IoT Supervisor (FastAPI - Single BACnet Authority)          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Config       │  │ BACnet       │  │ API Server     │  │
│  │ Interpreter  │  │ Client       │  │ (Port 8080)    │  │
│  └──────────────┘  └──────────────┘  └────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Device       │  │ Flow         │  │ Config         │  │
│  │ Discovery    │  │ Executor     │  │ Persistence    │  │
│  └──────────────┘  └──────────────┘  └────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SQLite: runtime.db (configs, device cache, data)     │  │
│  │ Built-in BACnet client: BACnet protocol operations   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ BACnet/IP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              BACnet Simulator (Development)                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Device      │  │ Virtual      │  │ BACnet Server  │  │
│  │ Models      │  │ Points       │  │ (Port 47808)   │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Production Mode (2-App architecture with direct deployment):

```
┌─────────────────────────────────────────────────────────────┐
│       BMS Designer (Next.js - Integrator's Laptop)         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Flow Editor │  │ Config Gen   │  │ Device Config    │  │
│  │ (React Flow)│  │ (Zod)        │  │ (IP:Port)        │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│                  Next.js (Port 3000)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SQLite: projects.db (local project storage)          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Direct HTTP API Call
                          │ POST http://device-ip:8080/api/config/deploy
                          ▼
┌─────────────────────────────────────────────────────────────┐
│   BYOD IoT Device (Raspberry Pi / Industrial PC)           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              BMS IoT Supervisor (Docker Container)          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ Config       │  │ BACnet       │  │ FastAPI  │  │  │
│  │  │ Persistence  │  │ Operations   │  │ (8080)   │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ Flow         │  │ Device       │  │ Health   │  │  │
│  │  │ Executor     │  │ Discovery    │  │ Status   │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │ SQLite: runtime.db                         │   │  │
│  │  │ - Deployed configurations                   │   │  │
│  │  │ - Device cache & discovery                  │   │  │
│  │  │ - Execution state & logs                    │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ BACnet/IP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BMS Devices & Sensors                    │
│  [HVAC] [Lighting] [Access Control] [Energy Meters] [IoT]  │
└─────────────────────────────────────────────────────────────┘

         User's Monitoring Tools (Optional)
┌─────────────────────────────────────────────────────────────┐
│  Third-Party Monitoring via IoT Supervisor Health APIs            │
│  http://[device-ip]:8080/api/health                        │
│  http://[device-ip]:8080/api/execution/status              │
└─────────────────────────────────────────────────────────────┘
```

**Supported Deployment Platforms**:

| Platform                | Use Case                        | Pros                                 | Cons                                |
| ----------------------- | ------------------------------- | ------------------------------------ | ----------------------------------- |
| **Balena.io** (Primary) | Production IoT fleet management | Enterprise features, OTA, monitoring | Third-party dependency, cost        |
| **Docker Swarm**        | Self-hosted fleet               | Full control, no external dependency | More complex setup, manual scaling  |
| **AWS IoT Greengrass**  | AWS ecosystem integration       | Scalable, ML capabilities            | AWS lock-in, complexity             |
| **Azure IoT Edge**      | Microsoft ecosystem             | Enterprise integration, hybrid cloud | Microsoft lock-in, cost             |
| **Manual Docker**       | Simple single-device deployment | Simple, no external dependencies     | No fleet management, manual updates |

**Deployment Workflow** (2-App Architecture):

1. BMS Designer → Create visual flow and generate JSON configuration
2. BMS Designer → Configure target device (IP:Port) in settings
3. BMS Designer → Click "Deploy" → Direct API call to IoT Supervisor
4. BMS IoT Supervisor → Receive config via API → Persist to SQLite → Start execution
5. User → Monitor via their own tools or third-party monitoring applications

### 3.4 BACnet Simulator Application

**Note**: We will use an existing BACnet simulator from our private repository and port it to the public repository for this project. This avoids reinventing the wheel and leverages proven simulation capabilities.

The BACnet Simulator provides a realistic development environment that closely mimics production BACnet/IP devices:

### 3.5 BACnet Client Package (IoT Supervisor Only)

The built-in BACnet client is used exclusively by BMS IoT Supervisor as the single source of truth for all BACnet operations:

```python
# IoT Supervisor BACnet client structure
class BACnetClient:
    """Unified BACnet client for device discovery and communication"""

    async def discover_devices(network_range: str = "auto") -> List[Device]:
        """Discover BACnet devices on network"""

    async def get_device_objects(device_id: int) -> List[BACnetObject]:
        """Get all objects for a specific device"""

    async def read_object(device_id: int, obj_type: str, instance: int) -> Any:
        """Read current value of BACnet object"""

    async def write_object(device_id: int, obj_type: str, instance: int, value: Any) -> bool:
        """Write value to BACnet object"""

    async def get_live_value(device_id: int, obj_type: str, instance: int) -> LiveDataResponse:
        """Get current value of BACnet object with status"""

    async def batch_read_objects(requests: List[ObjectRequest]) -> List[LiveDataResponse]:
        """Efficiently read multiple objects in a single operation"""

class Device:
    device_id: int
    device_name: str
    vendor_name: str
    model_name: str
    ip_address: str
    objects: List[BACnetObject]

class BACnetObject:
    object_type: str        # "analogInput", "binaryOutput", etc.
    object_instance: int
    object_name: str
    description: str
    units: str
    present_value: Any
```

**Package Usage**:

- **BMS IoT Supervisor Only**: All BACnet operations (discovery, read, write, polling)
- **BMS Designer**: Accesses BACnet data via IoT Supervisor's REST API, never directly
- **BACnet Simulator**: Creates virtual devices using same interface

### 3.6 BMS Designer Web Application (Next.js Standalone)

#### Component Architecture

```
apps/designer/
├── app/                        # Next.js App Router
│   ├── projects/
│   │   ├── page.tsx           # Projects list
│   │   └── [id]/
│   │       ├── page.tsx       # Flow editor
│   │       └── deploy/
│   │           └── page.tsx   # Deployment interface
│   ├── settings/
│   │   └── page.tsx           # Device configuration (IP:Port)
│   ├── api/                   # Next.js API Routes
│   │   ├── projects/          # Project CRUD (SQLite)
│   │   │   ├── route.ts       # GET (list), POST (create)
│   │   │   └── [id]/
│   │   │       └── route.ts   # GET, PUT, DELETE
│   │   ├── config/
│   │   │   └── generate/
│   │   │       └── route.ts   # Generate JSON config from flow
│   │   └── runtime/           # Proxy to IoT Supervisor API
│   │       └── [...path]/
│   │           └── route.ts   # Dynamic proxy to IoT Supervisor
│   ├── layout.tsx             # Root layout
│   └── globals.css            # Global styles
├── components/
│   ├── flow-editor/
│   │   ├── FlowCanvas.tsx
│   │   ├── NodeLibrary.tsx
│   │   ├── EdgeValidator.tsx
│   │   └── PropertyPanel.tsx
│   ├── project-management/
│   │   ├── ProjectList.tsx
│   │   ├── ProjectForm.tsx
│   │   └── ProjectExport.tsx
│   ├── deployment/
│   │   ├── DeviceConfig.tsx      # Configure IoT Supervisor device IP:Port
│   │   ├── DeployButton.tsx      # Deploy to configured device
│   │   └── DeployStatus.tsx      # Show deployment result
│   └── ui/                       # Reusable UI components
│       ├── Button.tsx
│       ├── Modal.tsx
│       └── DataTable.tsx
├── lib/
│   ├── db/
│   │   ├── client.ts          # better-sqlite3 wrapper
│   │   ├── projects.ts        # Project operations
│   │   └── migrations.ts      # Database migrations
│   ├── schemas/               # Generated from bms-schemas package
│   │   ├── flow-config.ts     # Generated Zod flow schemas
│   │   ├── project.ts         # Generated Zod project schemas
│   │   └── node-types.ts      # Generated Zod node schemas
│   ├── config/
│   │   └── generator.ts       # Flow to JSON converter
│   ├── runtime-client.ts      # HTTP client for IoT Supervisor API
│   ├── device-config.ts       # Device connection management
│   └── types/
│       ├── generated.ts       # Generated from Zod schemas
│       └── index.ts           # Manual type definitions
├── public/                    # Static assets
├── projects.db                # SQLite database (local storage)
├── package.json
├── next.config.js
└── tsconfig.json
```

#### Key Technologies

- **Next.js 15.5**: Standalone full-stack framework with App Router
- **TypeScript**: Type safety throughout
- **React Flow**: Visual programming canvas
- **Zod**: IoT Supervisor validation and schema definition
- **better-sqlite3**: SQLite database for project storage
- **Zustand**: Lightweight state management
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern component library built on Tailwind

### 3.7 BMS IoT Supervisor (Single BACnet Authority)

#### Component Architecture

```
apps/iot-supervisor-app/
├── main.py                     # FastAPI application entry point
├── api/
│   ├── devices.py              # BACnet device discovery & management
│   ├── points.py               # Read/write BACnet points
│   ├── execution.py            # Flow execution status & control
│   ├── monitoring.py           # Live data & time-series endpoints
│   ├── config.py               # Configuration deployment
│   └── health.py               # Health check & status endpoints
├── services/
│   ├── bacnet/
│   │   ├── discovery.py        # Device discovery service
│   │   ├── client.py           # BACnet client wrapper
│   │   ├── cache.py            # Device & object caching
│   │   └── polling.py          # Live value polling service
│   ├── execution/
│   │   ├── interpreter.py      # Configuration interpreter
│   │   ├── executor.py         # Node execution engine
│   │   ├── scheduler.py        # APScheduler integration
│   │   └── tracker.py          # Execution state tracking
│   └── data/
│       ├── collector.py        # Time-series data collection
│       └── storage.py          # SQLite data management
├── models/
│   ├── config_models.py        # Pydantic configuration models
│   ├── device_models.py        # BACnet device/object models
│   ├── execution_models.py     # Flow execution state models
│   └── api_models.py           # API request/response models
├── core/
│   ├── node_library.py         # Node type implementations
│   ├── context_manager.py      # Flow variable context
│   ├── error_handler.py        # Error handling & recovery
│   └── performance.py          # Metrics & monitoring
├── database/
│   ├── connection.py           # SQLite connection
│   ├── migrations/             # Database schema migrations
│   ├── repositories/           # Data access layer
│   │   ├── devices.py          # Device repository
│   │   ├── execution.py        # Execution data repository
│   │   └── timeseries.py       # Time-series repository
│   └── schemas.sql             # Database schema definitions
└── protocols/
    ├── bacnet/
    │   └── client.py           # Built-in BACnet client
    └── plugins/                # Future protocol plugins
        └── __init__.py         # Plugin interface definition
```

#### Key Technologies

- **Python 3.11+**: High-performance async runtime
- **FastAPI**: REST API framework (all BACnet & execution APIs)
- **Pydantic**: Data validation (basic structural validation)
- **Built-in BACnet Client**: Exclusive BACnet protocol operations
- **SQLite**: Device cache & time-series storage (24hr rolling)
- **APScheduler**: Cron-based flow scheduling
- **asyncio**: Async/await for concurrent operations

## 4. Two-Application Architecture Benefits

### 4.1 Why Separate Designer and IoT Supervisor?

The architecture separates visual programming and monitoring (BMS Designer) from execution (BMS Designer IoT Supervisor):

**Benefits**:

- **UI Consolidation**: Single sophisticated interface for both design and monitoring
- **Clean Separation**: Designer handles all UI, IoT Supervisor focuses purely on execution
- **Independent Operation**: IoT Supervisor operates autonomously with JSON configuration
- **Real-time Visualization**: Live execution tracking through API communication
- **Resource Efficiency**: IoT Supervisor optimized for IoT with minimal dependencies
- **Development Flexibility**: Test IoT Supervisor independently with exported configurations
- **Deployment Options**: Deploy Designer for monitoring or IoT Supervisor-only for headless operation

**How It Works**:

1. BMS Designer creates flows and generates JSON configuration
2. Designer directly deploys configuration to IoT Supervisor via API
3. IoT Supervisor persists configuration to its own SQLite database
4. Designer polls IoT Supervisor APIs for live monitoring and control
5. Users access Designer interface for configuration and monitoring

### 4.2 Deployment Workflow

```
BMS Integrator Workflow:
1. Design flow in BMS Designer (Next.js UI)
2. Configure target IoT Supervisor device (IP:Port) in settings
3. Click "Deploy" to send configuration via API
4. IoT Supervisor receives config and starts execution
5. Monitor live data and control via Designer interface
6. Balena deploys both Designer + IoT Supervisor containers to devices
7. Access monitoring via deployed Designer UI at http://[device-ip]:3000
8. Designer UI polls IoT Supervisor API for real-time execution visualization
```

**2-Tier Communication Flow**:

```
Next.js UI (Designer) → HTTP REST API → IoT Supervisor FastAPI → BACnet Devices
(Port 3000)                             (Port 8080)      (Port 47808)
```

**Direct API Deployment Benefits**:

- **Simplicity**: Direct API calls eliminate intermediate packaging steps
- **Real-time feedback**: Immediate deployment status and validation
- **Configuration persistence**: IoT Supervisor stores configs in SQLite automatically
- **Device management**: Configure multiple IoT Supervisor devices from Designer
- **Live monitoring**: Real-time data polling through HTTP REST APIs

## 5. Technical Design

### 5.1 React Flow to Configuration Pipeline

```
Visual Flow → Flow JSON → Configuration Schema → IoT Supervisor Interpretation
```

#### Detailed Pipeline Steps

1. **Visual Design Phase**

   - User drags nodes from palette onto canvas
   - Connects nodes with edges to define data flow
   - Configures node properties (thresholds, parameters)
   - Validates flow for completeness and correctness

2. **Flow Serialization**

   ```javascript
   {
     "id": "flow-001",
     "name": "HVAC Optimization",
     "nodes": [
       {
         "id": "sensor-1",
         "type": "sensor_read",
         "config": {
           "data_source": "device:bacnet:100:analogInput:1:presentValue",
           "alias": "temp_zone_1"
         }
       },
       {
         "id": "logic-1",
         "type": "threshold",
         "config": {
           "input": "temp_zone_1",
           "operator": ">",
           "value": 25,
           "output": "cooling_needed"
         }
       }
     ],
     "edges": [
       {
         "id": "e1-2",
         "source": "sensor-1",
         "target": "logic-1"
       }
     ]
   }
   ```

3. **Configuration Validation**

   ```json
   {
     "flow_id": "flow-001",
     "version": "1.0",
     "schedule": "*/5 * * * *",
     "execution_config": {
       "timeout": 30,
       "retry_count": 3,
       "error_handling": "continue"
     },
     "nodes": [...],
     "data_sources": {
       "temp_zone_1": {
         "protocol": "bacnet",
         "device": "100",
         "object": "analogInput:1:presentValue"
       }
     }
   }
   ```

4. **IoT Supervisor Interpretation**

   ```python
   class ConfigInterpreter:
       async def execute_flow(self, config):
           # No code generation - interpret on the fly
           context = {}

           for node in config['nodes']:
               if node['type'] == 'sensor_read':
                   value = await self.protocol.read_point(
                       node['config']['data_source']
                   )
                   context[node['config']['alias']] = value

               elif node['type'] == 'threshold':
                   input_val = context[node['config']['input']]
                   result = self.evaluate_condition(
                       input_val, node['config']['operator'], node['config']['value']
                   )
                   context[node['config']['output']] = result

           return context
   ```

### 5.2 Node Types and Configuration Execution

| Node Category   | Visual Node      | Configuration Schema                                                              | IoT Supervisor Execution               |
| --------------- | ---------------- | --------------------------------------------------------------------------------- | -------------------------------------- |
| **Input**       |                  |                                                                                   |                                        |
| BACnet Sensor   | Analog Input     | `{"type": "sensor_read", "data_source": "bacnet:100:AI1", "alias": "temp"}`       | Config interpreter calls BACnet plugin |
| Modbus Sensor   | Holding Register | `{"type": "sensor_read", "data_source": "modbus:1:40001", "alias": "pressure"}`   | Config interpreter calls Modbus plugin |
| Manual Input    | Number Input     | `{"type": "parameter", "name": "setpoint", "default": 22}`                        | Retrieved from runtime parameters      |
| Schedule        | Time Trigger     | `{"type": "trigger", "schedule": "*/5 * * * *"}`                                  | Cron scheduler executes flow           |
| **Logic**       |                  |                                                                                   |                                        |
| Comparison      | Greater Than     | `{"type": "threshold", "input": "temp", "operator": ">", "value": 25}`            | `context[input] > value`               |
| Boolean         | AND Gate         | `{"type": "and", "inputs": ["a", "b"], "output": "result"}`                       | `context[a] and context[b]`            |
| Math            | Calculator       | `{"type": "math", "expression": "a * 1.8 + 32", "output": "temp_f"}`              | Safe expression evaluation             |
| **Control**     |                  |                                                                                   |                                        |
| Conditional     | If/Else          | `{"type": "conditional", "condition": "cooling_needed", "true_flow": [...]}`      | Branch execution based on condition    |
| Loop            | For Each         | `{"type": "loop", "items": "device_list", "flow": [...]}`                         | Iterate execution over items           |
| Delay           | Timer            | `{"type": "delay", "seconds": 30}`                                                | `await asyncio.sleep(seconds)`         |
| **Output**      |                  |                                                                                   |                                        |
| BACnet Actuator | Binary Output    | `{"type": "actuator_write", "data_sink": "bacnet:100:BO1", "value": "$result"}`   | Config interpreter calls BACnet plugin |
| Modbus Actuator | Coil Write       | `{"type": "actuator_write", "data_sink": "modbus:1:coil:100", "value": "$state"}` | Config interpreter calls Modbus plugin |
| Alert           | Email Sender     | `{"type": "alert", "message": "Temperature high: $temp", "priority": "high"}`     | Send notification via alert service    |
| Logger          | Data Logger      | `{"type": "log", "data": {"temp": "$temp", "time": "$timestamp"}}`                | Store data in SQLite                   |
| **Extensions**  |                  |                                                                                   |                                        |
| Python Script   | Custom Logic     | `{"type": "python_script", "code": "# Custom algorithm", "inputs": [...]}`        | **Future**: Execute Python in sandbox  |

### 5.3 Data Flow Architecture

#### Deployment vs IoT Supervisor Data Flow

**Deployment-Time Data Flow** (One-time setup):

```
Designer DB → Direct API Call → IoT Supervisor Config Persistence
(projects.db)   (POST /api/config/deploy)   (runtime.db)
```

**IoT Supervisor Monitoring Data Flow** (Continuous):

```
BACnet Devices ←→ IoT Supervisor (FastAPI) ←── HTTP REST ──→ Designer (Next.js)
(Port 47808)       (Port 8080)                        (Port 3000)
                        │
                        ▼
                  SQLite (runtime.db)
                  (device cache, 24hr data)
```

**Communication Architecture**:

```
[Designer UI] ←── Next.js API Routes ──→ [IoT Supervisor API]
     │                    │                    │
     ▼                    ▼                    ▼
React State         SQLite (projects)    SQLite (runtime)
(UI state)          (project data)       (device cache, execution)
```

#### Control Flow Execution

```
1. Designer: User creates visual flow (React Flow)
2. Designer: Generate JSON configuration (Zod validation)
3. Designer: Save project to SQLite (better-sqlite3)
4. Designer: Deploy configuration directly to IoT Supervisor device (API call)
5. IoT Supervisor: Persist configuration to SQLite
6. IoT Supervisor: Receive and validate configuration (Pydantic)
7. IoT Supervisor: Start APScheduler with flow execution
8. IoT Supervisor: Execute nodes → BACnet operations (exclusive)
9. IoT Supervisor: Store execution state and time-series data
10. Designer: Poll IoT Supervisor API for monitoring data (HTTP)
11. Designer: Update UI with execution state
12. Users: Monitor via web UI at http://[device-ip]:3000
```

#### API Communication Pattern

**Designer → IoT Supervisor (HTTP REST)**:

```typescript
// Designer: runtime-client.ts
async function getDevices(): Promise<Device[]> {
  const response = await fetch("http://runtime:8080/api/devices");
  return response.json();
}

async function readPoints(points: string[]): Promise<PointValues> {
  const response = await fetch("http://runtime:8080/api/points/read", {
    method: "POST",
    body: JSON.stringify({ points }),
  });
  return response.json();
}
```

**IoT Supervisor: Single BACnet Authority**:

```python
# IoT Supervisor: api/devices.py
@router.get("/devices")
async def get_devices():
    """IoT Supervisor is the ONLY source for BACnet devices"""
    devices = await bacnet_service.discover_devices()
    cache_service.update_devices(devices)
    return devices

@router.post("/points/read")
async def read_points(request: PointReadRequest):
    """All BACnet reads go through IoT Supervisor"""
    values = await bacnet_service.batch_read(request.points)
    return values
```

### 5.4 Polling Configuration and Strategy

**Polling Intervals by Use Case**:

| Use Case                            | Interval               | Justification                           |
| ----------------------------------- | ---------------------- | --------------------------------------- |
| **Designer → IoT Supervisor API**   | 2-5 seconds            | Monitoring dashboard updates            |
| **IoT Supervisor Device Discovery** | On-demand + 60 seconds | Manual trigger + periodic cache refresh |
| **IoT Supervisor → BACnet Devices** | 1-30 seconds           | Configurable based on flow requirements |
| **Execution State Updates**         | 500ms - 2 seconds      | Real-time execution visualization       |
| **System Health Checks**            | 10 seconds             | Health monitoring, error detection      |
| **Time-series Collection**          | Flow-specific          | Based on node configuration             |

**Polling Implementation**:

```python
class PollingManager:
    def __init__(self, bacnet_client: BACnetClient):
        self.client = bacnet_client
        self.polling_tasks = {}

    async def start_polling(self, poll_config: PollingConfig):
        """Start polling for specific objects"""
        task = asyncio.create_task(
            self._poll_loop(poll_config.objects, poll_config.interval_ms)
        )
        self.polling_tasks[poll_config.id] = task

    async def _poll_loop(self, objects: List[ObjectRequest], interval_ms: int):
        while True:
            results = await self.client.batch_read_objects(objects)
            await self._update_cache(results)
            await asyncio.sleep(interval_ms / 1000)

class PollingConfig:
    id: str
    objects: List[ObjectRequest]
    interval_ms: int
    enabled: bool
```

**Efficiency Strategies**:

- **Batch Reading**: Group multiple object reads into single BACnet requests
- **Smart Polling**: Only poll objects visible in UI or used in active flows
- **Adaptive Intervals**: Slow down polling when values are stable
- **Error Backoff**: Increase intervals for devices with communication errors

## 6. Schema Management and Validation

### 6.1 Shared Schema Validation Approach

The system uses a **shared schema package** for consistent validation across both applications. JSON Schema serves as the source of truth, generating both Zod (TypeScript) and Pydantic (Python) validation.

```
User Input → Designer (Generated Zod) → IoT Supervisor (Generated Pydantic) → BACnet Operations
              ↓                           ↓
         Full Validation            Structural Validation
              ↑                           ↑
         Generated from JSON Schema ──────┘
```

**Validation Strategy**:

1. **Source of Truth**: JSON Schema definitions in `packages/bms-schemas`
2. **Designer**: Uses generated Zod schemas for comprehensive validation
3. **IoT Supervisor**: Uses generated Pydantic models for structural validation
4. **Type Safety**: Both TypeScript and Python types generated from same source
5. **Consistency**: Schema updates automatically propagate to both applications

### 6.2 Designer Validation (Generated Zod)

**Generated Validation Schemas** (from `packages/bms-schemas`):

```typescript
// lib/schemas/flow-config.ts
import { z } from "zod";

const BACnetObjectType = z.enum([
  "analogInput",
  "analogOutput",
  "binaryInput",
  "binaryOutput",
]);

const BACnetReadConfig = z.object({
  device_id: z.number().min(0).max(4194303),
  object_type: BACnetObjectType,
  object_instance: z.number().min(0).max(4194303),
  poll_interval_ms: z.number().min(1000).max(60000).default(5000),
  alias: z.string().regex(/^[a-zA-Z][a-zA-Z0-9_]*$/),
});

const ThresholdConfig = z.object({
  input: z.string().min(1),
  operator: z.enum([">", "<", ">=", "<=", "==", "!="]),
  value: z.union([z.number(), z.string()]),
  output: z.string().regex(/^[a-zA-Z][a-zA-Z0-9_]*$/),
});

const NodeConfiguration = z.object({
  id: z.string().regex(/^[a-zA-Z0-9_-]+$/),
  type: z.string(),
  position: z.object({ x: z.number(), y: z.number() }),
  config: z.union([BACnetReadConfig, ThresholdConfig, z.record(z.any())]),
});

export const FlowConfiguration = z
  .object({
    metadata: z.object({
      flow_id: z.string().uuid(),
      flow_name: z.string().min(1).max(100),
      version: z.string().regex(/^\d+\.\d+\.\d+$/),
    }),
    nodes: z.array(NodeConfiguration),
    connections: z.array(
      z.object({
        source: z.string(),
        target: z.string(),
        sourceHandle: z.string().optional(),
        targetHandle: z.string().optional(),
      }),
    ),
  })
  .refine(
    (data) => {
      // Complex validation: ensure connections reference valid nodes
      const nodeIds = new Set(data.nodes.map((n) => n.id));
      return data.connections.every(
        (c) => nodeIds.has(c.source) && nodeIds.has(c.target),
      );
    },
    { message: "Invalid connection references" },
  );

// Infer TypeScript types
export type FlowConfiguration = z.infer<typeof FlowConfiguration>;
export type NodeConfiguration = z.infer<typeof NodeConfiguration>;
```

### 6.3 IoT Supervisor Validation (Pydantic)

**Basic Structural Validation**:

```python
# models/config_models.py
from pydantic import BaseModel
from typing import List, Dict, Any

class FlowConfiguration(BaseModel):
    """Simple validation - trust Designer's comprehensive checks"""
    metadata: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    execution_config: Dict[str, Any] = {}

    class Config:
        extra = "forbid"  # Prevent unknown fields

class DeploymentPackage(BaseModel):
    """Validate deployment structure"""
    version: str
    configuration: FlowConfiguration
    project_id: str
    deployed_at: str

# IoT Supervisor focuses on execution, not validation
async def deploy_configuration(config_json: str):
    """Receive pre-validated configuration from Designer"""
    try:
        # Basic structure check
        package = DeploymentPackage.parse_raw(config_json)

        # Initialize database
        await init_runtime_database(package.configuration)

        # Start execution
        await executor.load_configuration(package.configuration.dict())

        return {"status": "deployed", "project_id": package.project_id}

    except ValidationError as e:
        # Only catches major structural issues
        logger.error(f"Invalid configuration structure: {e}")
        raise
```

### 6.4 Multi-Stage Validation Pipeline

**1. Design-Time Validation (Frontend)**:

```typescript
// Generated TypeScript types from Pydantic models
interface FlowConfiguration {
  metadata: Record<string, any>;
  nodes: NodeConfiguration[];
  connections: Connection[];
  execution_config?: Record<string, any>;
}

// Real-time validation using generated JSON schema
import { validateFlowConfig } from "./validators/generated";

const validateNodeConfig = (node: NodeConfiguration): ValidationResult => {
  return validateFlowConfig.validateNode(node);
};
```

**2. Pre-Deployment Validation (Designer → IoT Supervisor)**:

```python
# bms-deploy/validators.py
async def validate_deployment_package(config_path: str) -> ValidationResult:
    """Validate configuration using Pydantic models before deployment"""

    try:
        with open(config_path) as f:
            raw_config = json.load(f)

        # Pydantic validation with custom validators
        config = FlowConfiguration(**raw_config)

        # Additional deployment checks
        await validate_device_connectivity(config)
        await validate_resource_requirements(config)

        return ValidationResult(valid=True)

    except ValidationError as e:
        return ValidationResult(valid=False, errors=e.errors())
```

**3. IoT Supervisor Validation (IoT Supervisor Backend)**:

```python
# runtime/config_loader.py
class ConfigurationLoader:
    def load_and_validate(self, deployment_package: dict) -> FlowConfiguration:
        """IoT Supervisor configuration loading with Pydantic validation"""

        config_data = deployment_package['configuration']

        # Use same Pydantic models for runtime validation
        config = FlowConfiguration(**config_data)

        # IoT Supervisor-specific validation
        self.validate_runtime_capabilities(config)

        return config
```

## 6.5 Communication Architecture

### HTTP REST Communication

**Architecture Pattern**:

```
Designer (Next.js) ←── HTTP REST ──→ IoT Supervisor (FastAPI) ←── BACnet ──→ Devices
```

**Request/Response Flow**:

```typescript
// Designer: lib/runtime-client.ts
class IoT SupervisorClient {
  private baseUrl = 'http://localhost:8080'; // or runtime container IP

  async getDevices(): Promise<Device[]> {
    const response = await fetch(`${this.baseUrl}/api/devices`);
    return response.json();
  }

  async readPoints(points: string[]): Promise<PointValues> {
    const response = await fetch(`${this.baseUrl}/api/points/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ points })
    });
    return response.json();
  }

  async deployConfig(config: FlowConfiguration): Promise<DeployResult> {
    // Validate with Zod first
    const validated = FlowConfiguration.parse(config);

    const response = await fetch(`${this.baseUrl}/api/config/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validated)
    });
    return response.json();
  }
}
```

**Polling Strategy**:

```typescript
// Real-time monitoring with polling
export function useExecutionState(flowId: string) {
  const [state, setState] = useState<ExecutionState | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const newState = await runtime.getExecutionState(flowId);
        setState(newState);
      } catch (error) {
        console.error("Failed to poll execution state:", error);
      }
    }, 2000); // 2 second polling

    return () => clearInterval(interval);
  }, [flowId]);

  return state;
}
```

**Error Handling & Retry**:

```typescript
// Robust error handling
async function apiCall<T>(request: () => Promise<T>): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      return await request();
    } catch (error) {
      lastError = error as Error;

      if (attempt < 3) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * attempt));
      }
    }
  }

  throw lastError!;
}
```

**Advantages of HTTP Approach**:

- Simple request/response pattern
- Easy debugging with browser DevTools
- Standard REST endpoints
- Good enough latency for BMS applications (1-5 second updates)
- No additional infrastructure (brokers, etc.)

**Future Enhancement: MQTT Option**:

- Add MQTT for real-time event streaming
- Use for high-frequency updates (sub-second)
- Implement as optional enhancement
- Keep HTTP as fallback

### 6.4 Shared Schema Package (`packages/bms-schemas`)

**Package Structure**:

```
packages/bms-schemas/
├── package.json              # TypeScript tooling and exports
├── pyproject.toml           # Python generation scripts
├── schemas.json             # Single source of truth schemas
├── scripts/
│   ├── generate-typescript.js  # JSON Schema → Zod + Types
│   └── generate-python.py     # JSON Schema → Pydantic
├── typescript/              # Generated TypeScript exports
│   ├── index.ts            # Main exports
│   ├── schemas.ts          # Zod schemas
│   └── types.ts            # TypeScript interfaces
└── python/                  # Generated Python exports
    ├── __init__.py         # Main exports
    └── models.py           # Pydantic models
```

**Code Generation Workflow**:

```
schemas.json → generate-typescript.js → typescript/ (Zod + Types)
            └→ generate-python.py    → python/ (Pydantic)
```

**Usage in Apps**:

```typescript
// apps/designer - uses generated Zod
import { FlowConfigSchema } from "bms-schemas";
const result = FlowConfigSchema.parse(userInput);
```

```python
# apps/runtime - uses generated Pydantic
from bms_schemas import FlowConfiguration
config = FlowConfiguration.model_validate(json_data)
```

## 7. Testing Framework

### 7.1 Testing Architecture Overview

Multi-layer testing strategy ensures reliability at every level:

```
Unit Tests → Integration Tests → Configuration Tests → E2E Tests
    ↓              ↓                    ↓                 ↓
Components    API & BACnet       Config Generation    Full Flow
& Functions    Communication         & Validation      Execution
```

### 7.2 Frontend Testing

**Jest Configuration for React + TypeScript**:

```javascript
// jest.config.js
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  collectCoverageFrom: ["src/**/*.{ts,tsx}", "!src/**/*.d.ts"],
};
```

**React Flow Component Testing**:

```typescript
// FlowEditor.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { FlowEditor } from './FlowEditor';
import { mockBACnetDevices } from '../__mocks__/bacnet';

describe('FlowEditor', () => {
  it('validates node connections', () => {
    const { getByTestId } = render(<FlowEditor />);

    // Add two nodes
    fireEvent.click(getByTestId('add-node-bacnet-read'));
    fireEvent.click(getByTestId('add-node-threshold'));

    // Try to connect incompatible types
    const sourceHandle = getByTestId('node-1-output-string');
    const targetHandle = getByTestId('node-2-input-number');

    fireEvent.dragStart(sourceHandle);
    fireEvent.drop(targetHandle);

    // Should show type mismatch error
    expect(screen.getByText(/Type mismatch/)).toBeInTheDocument();
  });

  it('validates BACnet device configuration', async () => {
    const { getByTestId } = render(
      <FlowEditor bacnetDevices={mockBACnetDevices} />
    );

    fireEvent.click(getByTestId('add-node-bacnet-read'));

    // Enter invalid device ID
    fireEvent.change(getByTestId('device-id-input'), {
      target: { value: '99999' }
    });

    // Should show validation error
    expect(await screen.findByText(/Device not found/)).toBeInTheDocument();
  });
});
```

### 7.3 Backend Testing

**Pytest Configuration for FastAPI + Async**:

```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.bacnet_client import BACnetClient

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def bacnet_client():
    client = BACnetClient()
    await client.initialize()
    yield client
    await client.close()

@pytest.fixture
def mock_bacnet_device(monkeypatch):
    """Mock BACnet device for testing"""
    mock_device = {
        'device_id': 100,
        'device_name': 'Test Device',
        'objects': [
            {'type': 'analogInput', 'instance': 1, 'name': 'Temperature'}
        ]
    }
    monkeypatch.setattr('app.bacnet_client.discover_devices',
                       lambda: [mock_device])
    return mock_device
```

**API Endpoint Testing**:

```python
# test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_configuration_generation(client: AsyncClient):
    """Test configuration generation with validation"""

    flow_data = {
        "nodes": [
            {
                "id": "node-1",
                "type": "bacnet_read",
                "config": {
                    "device_id": 100,
                    "object_type": "analogInput",
                    "object_instance": 1
                }
            }
        ],
        "connections": []
    }

    response = await client.post("/api/generate-config", json=flow_data)
    assert response.status_code == 200

    config = response.json()
    assert config['metadata']['version']
    assert len(config['nodes']) == 1
    assert config['nodes'][0]['type'] == 'bacnet_read'

@pytest.mark.asyncio
async def test_invalid_configuration(client: AsyncClient):
    """Test validation catches invalid configurations"""

    invalid_flow = {
        "nodes": [
            {
                "id": "node-1",
                "type": "bacnet_read",
                "config": {
                    "device_id": -1,  # Invalid device ID
                    "object_type": "invalid_type"
                }
            }
        ]
    }

    response = await client.post("/api/generate-config", json=invalid_flow)
    assert response.status_code == 422
    assert "validation_error" in response.json()
```

### 7.4 Configuration Testing

**Schema Validation Tests**:

```python
# test_config_validation.py
import pytest
from pydantic import ValidationError
from app.models import FlowConfiguration, NodeConfig

def test_valid_configuration():
    """Test valid configuration passes all checks"""

    config_data = {
        "metadata": {
            "flow_id": "550e8400-e29b-41d4-a716-446655440000",
            "version": "1.0.0"
        },
        "nodes": [
            {
                "id": "temp-sensor",
                "type": "bacnet_read",
                "config": {
                    "device_id": 100,
                    "object_type": "analogInput",
                    "object_instance": 1
                }
            }
        ],
        "connections": []
    }

    config = FlowConfiguration(**config_data)
    assert config.metadata.version == "1.0.0"
    assert len(config.nodes) == 1

def test_invalid_device_id():
    """Test validation rejects invalid device IDs"""

    config_data = {
        "metadata": {"flow_id": "test", "version": "1.0.0"},
        "nodes": [
            {
                "id": "node-1",
                "type": "bacnet_read",
                "config": {
                    "device_id": 5000000,  # Exceeds max BACnet device ID
                    "object_type": "analogInput",
                    "object_instance": 1
                }
            }
        ],
        "connections": []
    }

    with pytest.raises(ValidationError) as exc_info:
        FlowConfiguration(**config_data)

    assert "device_id" in str(exc_info.value)

def test_circular_dependency_detection():
    """Test circular dependency detection in connections"""

    config_data = {
        "metadata": {"flow_id": "test", "version": "1.0.0"},
        "nodes": [
            {"id": "A", "type": "math", "config": {}},
            {"id": "B", "type": "math", "config": {}},
            {"id": "C", "type": "math", "config": {}}
        ],
        "connections": [
            {"from_node": "A", "to_node": "B"},
            {"from_node": "B", "to_node": "C"},
            {"from_node": "C", "to_node": "A"}  # Creates cycle
        ]
    }

    config = FlowConfiguration(**config_data)
    validator = DeploymentValidator()

    result = validator.validate_deployment(config)
    assert not result.valid
    assert "circular dependencies" in result.errors[0]
```

**Configuration Generation Tests**:

```python
# test_config_generation.py
def test_config_generation_preserves_types():
    """Test type preservation during config generation"""

    generator = ConfigurationGenerator()

    flow = {
        "nodes": [
            {
                "id": "threshold",
                "type": "comparison",
                "config": {
                    "operator": ">",
                    "value": 25.5,  # Float value
                    "threshold_type": "number"
                }
            }
        ]
    }

    config = generator.generate(flow)

    # Ensure float is preserved, not converted to int
    assert isinstance(config['nodes'][0]['config']['value'], float)
    assert config['nodes'][0]['config']['value'] == 25.5
```

## 8. Data Models

### 8.1 Core Data Structures

#### Desktop App Database Schema

**Projects Table**:

```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Project Configs Table**:

```sql
CREATE TABLE project_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    flow_data JSON NOT NULL,      -- React Flow state (nodes, edges, viewport)
    config_json JSON NOT NULL,    -- Generated configuration for IoT deployment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**BACnet Objects Table**:

```sql
CREATE TABLE bacnet_objects (
    device_id INTEGER,
    object_type TEXT,
    object_instance INTEGER,
    object_name TEXT,
    description TEXT,
    units TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (device_id, object_type, object_instance)
);
```

#### Flow Definition (TypeScript Interface)

```typescript
interface Project {
  id: string;
  name: string;
  description: string;
  created_at: DateTime;
  updated_at: DateTime;
}

interface ProjectConfig {
  id: number;
  project_id: string;
  flow_data: ReactFlowState; // Complete React Flow editor state
  config_json: FlowConfiguration; // Generated IoT configuration
  created_at: DateTime;
}

interface ReactFlowState {
  nodes: Node[];
  edges: Edge[];
  viewport: { x: number; y: number; zoom: number };
}

interface CachedBACnetObject {
  device_id: number;
  object_type: string;
  object_instance: number;
  object_name: string;
  description?: string;
  units?: string;
  discovered_at: DateTime;
}

interface Node {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
  inputs: Port[];
  outputs: Port[];
}

interface Edge {
  id: string;
  source: string;
  sourceHandle?: string;
  target: string;
  targetHandle?: string;
  data?: {
    condition?: string;
    transform?: string;
  };
}
```

#### Flow Configuration Schema

```typescript
// Generated configuration structure
interface FlowConfiguration {
  metadata: {
    flow_id: string;
    flow_name: string;
    version: string;
    generated_at: DateTime;
  };
  execution: {
    schedule?: {
      cron: string;
      timezone: string;
    };
    triggers: TriggerConfig[];
    error_handling: {
      retry_count: number;
      timeout_ms: number;
      on_failure: "stop" | "continue" | "alert";
    };
  };
  nodes: NodeConfiguration[];
  connections: ConnectionConfiguration[];
}

interface NodeConfiguration {
  id: string;
  type: string;
  config: Record<string, any>;
  runtime_options: {
    timeout_ms?: number;
    retry_count?: number;
    parallel?: boolean;
  };
}

interface ConnectionConfiguration {
  from_node: string;
  from_output: string;
  to_node: string;
  to_input: string;
  transform?: {
    script?: string; // Python script for data transformation
    mapping?: Record<string, string>;
  };
}

interface TriggerConfig {
  type: "schedule" | "device_event" | "data_change" | "external_api";
  config: Record<string, any>;
}
```

#### Data Source Configuration

```typescript
// Unified data source abstraction
interface DataSource {
  id: string;
  name: string;
  pattern: "device_point" | "message_topic" | "service_api";
  protocol: string; // 'bacnet', 'mqtt', 'lora', etc.

  // Device/Point pattern (BACnet, LoRa, Modbus)
  device_config?: {
    device_id: string;
    point_id: string; // "analogInput:123:presentValue" for BACnet
    connection: {
      ip_address?: string;
      port?: number;
      device_instance?: number;
    };
  };

  // Message/Topic pattern (MQTT, AMQP)
  topic_config?: {
    topic: string; // "building/zone1/temperature"
    qos?: number;
    retained?: boolean;
    connection: {
      broker_host: string;
      broker_port: number;
      username?: string;
      password?: string;
    };
  };

  // Service/API pattern (HTTP REST, GraphQL)
  service_config?: {
    endpoint: string;
    method: "GET" | "POST" | "PUT";
    headers?: Record<string, string>;
    connection: {
      base_url: string;
      auth?: {
        type: "bearer" | "basic" | "api_key";
        token: string;
      };
    };
  };

  // Common properties
  data_type: "float" | "integer" | "boolean" | "string";
  unit?: string;
  scale?: number;
  offset?: number;
  status: "active" | "inactive" | "error";
  last_updated: DateTime;
}
```

#### Execution Context

```typescript
interface ExecutionContext {
  flow_id: string;
  instance_id: string;
  started_at: DateTime;
  state: "running" | "paused" | "stopped" | "error";
  variables: Map<string, any>;
  metrics: {
    execution_time_ms: number;
    memory_usage_mb: number;
    device_reads: number;
    device_writes: number;
  };
  errors: Error[];
}
```

#### Deployment Package Models

```typescript
interface DeploymentPackage {
  project_id: string;
  project_name: string;
  config_json: ProjectConfiguration;
  bacnet_objects: BACnetObject[]; // Discovered objects for IoT Supervisor DB initialization
  docker_compose: string; // Generated docker-compose.yml
  environment_vars: EnvConfig;
  deployment_target: string; // 'balena', 'docker', 'manual'
  created_at: DateTime;
  checksum: string; // For integrity validation
}

interface EnvConfig {
  BACNET_DEVICE_ID: number;
  BACNET_INTERFACE: string;
  LOG_LEVEL: string;
  MONITORING_PORT: number;
  DATA_RETENTION_HOURS: number;
  [key: string]: string | number;
}

interface DeploymentStatus {
  deployment_id: string;
  project_id: string;
  target_device: string;
  status: "pending" | "deploying" | "success" | "failed" | "rollback";
  progress_percentage: number;
  started_at: DateTime;
  completed_at?: DateTime;
  error_message?: string;
  rollback_available: boolean;
}

interface ExecutionState {
  flow_id: string;
  status: "idle" | "running" | "paused" | "error" | "completed";
  current_executing_nodes: string[]; // Node IDs currently executing
  execution_start_time: DateTime;
  execution_context: Record<string, any>; // Current variable values
  total_nodes: number;
  completed_nodes: number;
  failed_nodes: string[];
  execution_timeline: NodeExecutionEvent[];
}

interface NodeExecutionStatus {
  node_id: string;
  status: "idle" | "executing" | "completed" | "error" | "skipped";
  start_time?: DateTime;
  end_time?: DateTime;
  execution_duration_ms?: number;
  error_message?: string;
  input_values?: Record<string, any>;
  output_values?: Record<string, any>;
}

interface NodeExecutionEvent {
  node_id: string;
  event_type: "started" | "completed" | "error";
  timestamp: DateTime;
  duration_ms?: number;
  error_details?: string;
}
```

#### IoT Supervisor Database Initialization

When deployed, BMS Designer IoT Supervisor initializes its own SQLite database from the deployment package:

```python
# IoT Supervisor startup process
def initialize_runtime_database(deployment_package: DeploymentPackage):
    # 1. Create clean SQLite database
    # 2. Import project configuration
    # 3. Seed bacnet_objects table from deployment package
    # 4. Initialize time-series storage schema
    # 5. Validate configuration integrity
    pass
```

This ensures IoT Supervisor operates independently with its own data copy, while Designer maintains the master project database.

### 8.2 Message Formats

#### HTTP Polling API Responses

```typescript
// Live data polling response
interface LiveDataResponse {
  timestamp: DateTime;
  device_id: number;
  object_type: string;
  object_instance: number;
  present_value: any;
  status: "ok" | "error" | "timeout";
}

// Flow status polling response
interface FlowStatusResponse {
  flow_id: string;
  status: "running" | "stopped" | "error";
  last_execution: DateTime;
  execution_count: number;
  error_message?: string;
}

// Device discovery polling response
interface DeviceDiscoveryResponse {
  devices: Device[];
  last_scan: DateTime;
  scan_status: "complete" | "in_progress" | "error";
}

// Real-time execution state response (for visual debugging)
interface ExecutionStateResponse {
  execution_state: ExecutionState;
  node_statuses: NodeExecutionStatus[];
  live_context: Record<string, any>; // Current variable values
  performance_metrics: {
    avg_execution_time_ms: number;
    nodes_per_second: number;
    memory_usage_mb: number;
  };
}

// Node execution events stream
interface NodeExecutionEventResponse {
  events: NodeExecutionEvent[];
  total_events: number;
  since_timestamp: DateTime;
}
```

## 9. Multi-Pattern Protocol Plugin Architecture

### 9.1 Protocol Communication Patterns

Different protocols use fundamentally different communication models:

| Pattern            | Protocols            | Communication Model                          | Use Case                          |
| ------------------ | -------------------- | -------------------------------------------- | --------------------------------- |
| **Device/Point**   | BACnet, Modbus, LoRa | Request specific data from addressed devices | Traditional BMS devices, PLCs     |
| **Pub/Sub Topics** | MQTT, AMQP           | Subscribe to data streams by topic           | IoT sensors, event-driven systems |
| **Service APIs**   | HTTP REST, GraphQL   | Call endpoints for data/actions              | Cloud services, external systems  |

### 9.2 Base Protocol Plugin Interface

All protocols inherit from a common base:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class ProtocolPattern(Enum):
    DEVICE_POINT = "device_point"
    MESSAGE_TOPIC = "message_topic"
    SERVICE_API = "service_api"

class ProtocolPlugin(ABC):
    """Base class for all protocol implementations"""

    @abstractmethod
    def get_pattern(self) -> ProtocolPattern:
        """Return the communication pattern this protocol uses"""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the protocol with configuration"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown of protocol connections"""
        pass

    @abstractmethod
    def get_protocol_info(self) -> Dict[str, Any]:
        """Return protocol metadata and capabilities"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if protocol connection is healthy"""
        pass
```

### 9.3 Device/Point Pattern (BACnet, LoRa)

For protocols that communicate with addressable devices:

```python
from dataclasses import dataclass
from typing import List, Callable

@dataclass
class DeviceInfo:
    device_id: str
    name: str
    ip_address: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class PointValue:
    point_id: str
    value: Any
    timestamp: float
    quality: str  # 'good', 'uncertain', 'bad'

class DeviceProtocol(ProtocolPlugin):
    """Interface for device/point based protocols"""

    def get_pattern(self) -> ProtocolPattern:
        return ProtocolPattern.DEVICE_POINT

    @abstractmethod
    async def discover_devices(self, timeout: int = 30) -> List[DeviceInfo]:
        """Discover devices on the network"""
        pass

    @abstractmethod
    async def read_point(self, device_id: str, point_id: str) -> PointValue:
        """Read a single point from a device"""
        pass

    @abstractmethod
    async def write_point(self, device_id: str, point_id: str, value: Any) -> bool:
        """Write a value to a point"""
        pass

    @abstractmethod
    async def read_multiple(self, device_id: str, point_ids: List[str]) -> List[PointValue]:
        """Read multiple points efficiently"""
        pass

    @abstractmethod
    async def poll_point(self, device_id: str, point_id: str) -> PointValue:
        """Poll single point value"""
        pass
```

### 9.4 Message/Topic Pattern (MQTT)

For publish/subscribe messaging protocols:

```python
@dataclass
class TopicMessage:
    topic: str
    payload: Any
    timestamp: float
    qos: int
    retained: bool

class MessageProtocol(ProtocolPlugin):
    """Interface for pub/sub messaging protocols"""

    def get_pattern(self) -> ProtocolPattern:
        return ProtocolPattern.MESSAGE_TOPIC

    @abstractmethod
    async def publish(self, topic: str, payload: Any,
                     qos: int = 0, retain: bool = False) -> bool:
        """Publish a message to a topic"""
        pass

    @abstractmethod
    async def poll_topic(self, topic: str) -> Optional[TopicMessage]:
        """Poll latest message from topic"""
        pass

    @abstractmethod
    async def poll_multiple_topics(self, topics: List[str]) -> List[TopicMessage]:
        """Poll multiple topics efficiently"""
        pass
```

### 9.5 Service API Pattern (HTTP, GraphQL)

For request/response service protocols:

```python
@dataclass
class ServiceRequest:
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Optional[Any]

@dataclass
class ServiceResponse:
    status_code: int
    headers: Dict[str, str]
    body: Any
    timestamp: float

class ServiceProtocol(ProtocolPlugin):
    """Interface for service API protocols"""

    def get_pattern(self) -> ProtocolPattern:
        return ProtocolPattern.SERVICE_API

    @abstractmethod
    async def request(self, request: ServiceRequest) -> ServiceResponse:
        """Make a service request"""
        pass

    @abstractmethod
    async def configure_endpoint(self, name: str, config: Dict[str, Any]) -> None:
        """Configure a named endpoint for reuse"""
        pass

    @abstractmethod
    async def call_endpoint(self, endpoint_name: str, params: Dict[str, Any]) -> ServiceResponse:
        """Call a preconfigured endpoint"""
        pass
```

### 9.6 BACnet/IP Implementation (Primary Protocol)

```python
class BACnetPlugin(DeviceProtocol):
    """BACnet/IP implementation using bacpypes3 and BAC0"""

    def __init__(self):
        self.bacnet_app = None  # bacpypes3 for low-level operations
        self.bac0_network = None  # BAC0 for high-level operations
        self.devices = {}

    async def initialize(self, config: Dict[str, Any]) -> None:
        # Initialize bacpypes3 for protocol operations
        self.bacnet_app = await create_bacnet_app(
            ip=config.get('ip_address', '0.0.0.0'),
            port=config.get('port', 47808)
        )

        # Initialize BAC0 for device management
        self.bac0_network = BAC0.connect(
            ip=config.get('ip_address'),
            port=config.get('port', 47808)
        )

    async def discover_devices(self, timeout: int = 30) -> List[DeviceInfo]:
        # Use bacpypes3 WhoIsRequest for discovery
        devices = await self.bacnet_app.who_is(timeout=timeout)

        # Get detailed info with BAC0
        device_list = []
        for device in devices:
            try:
                bac0_device = self.bac0_network[f'{device.instance}:device']
                device_list.append(DeviceInfo(
                    device_id=str(device.instance),
                    name=bac0_device.objectName,
                    ip_address=str(device.address),
                    metadata={
                        'vendor': bac0_device.vendorName,
                        'model': bac0_device.modelName,
                        'object_count': len(bac0_device.objects)
                    }
                ))
            except Exception as e:
                # Fallback for devices that don't respond to detailed queries
                device_list.append(DeviceInfo(
                    device_id=str(device.instance),
                    name=f'BACnet Device {device.instance}',
                    ip_address=str(device.address),
                    metadata={'discovery_error': str(e)}
                ))
        return device_list

    async def read_point(self, device_id: str, point_id: str) -> PointValue:
        # Parse BACnet object reference: "analogInput:123:presentValue"
        obj_type, obj_instance, prop_name = point_id.split(':')

        # Use BAC0 for high-level read
        device = self.bac0_network[f'{device_id}:device']
        value = device[f'{obj_type}:{obj_instance}.{prop_name}']

        return PointValue(
            point_id=point_id,
            value=value,
            timestamp=time.time(),
            quality='good' if value is not None else 'bad'
        )

    async def write_point(self, device_id: str, point_id: str, value: Any) -> bool:
        obj_type, obj_instance, prop_name = point_id.split(':')

        # Use BAC0 for write operation
        device = self.bac0_network[f'{device_id}:device']
        device[f'{obj_type}:{obj_instance}.{prop_name}'] = value
        return True
```

### 9.7 Modbus Implementation Example

```python
# File: plugins/modbus_plugin.py
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
import ipaddress

class ModbusPlugin(DeviceProtocol):
    """Modbus TCP/RTU protocol implementation"""

    def __init__(self):
        self.clients = {}  # device_id -> client mapping

    async def initialize(self, config: Dict[str, Any]) -> None:
        self.default_port = config.get('port', 502)
        self.timeout = config.get('timeout', 5)

    async def discover_devices(self, timeout: int = 30) -> List[DeviceInfo]:
        # Modbus discovery via network scanning
        network = config.get('network', '192.168.1.0/24')
        devices = []

        for ip in ipaddress.IPv4Network(network):
            try:
                client = AsyncModbusTCPClient(str(ip), port=self.default_port)
                await client.connect()

                # Try to read device identification (if supported)
                result = await client.read_device_information()
                if not result.isError():
                    devices.append(DeviceInfo(
                        device_id=str(ip),
                        name=result.information.get('ProductName', f'Modbus Device {ip}'),
                        ip_address=str(ip),
                        metadata={
                            'vendor': result.information.get('VendorName'),
                            'version': result.information.get('MajorMinorRevision')
                        }
                    ))
                await client.close()
            except:
                continue
        return devices

    async def read_point(self, device_id: str, point_id: str) -> PointValue:
        # Parse "holding_register:40001" or "coil:123" or "input_register:30001"
        register_type, address = point_id.split(':')
        address = int(address)

        client = await self._get_client(device_id)

        try:
            if register_type == 'holding_register':
                result = await client.read_holding_registers(address, 1, unit=1)
                value = result.registers[0] if not result.isError() else None
            elif register_type == 'input_register':
                result = await client.read_input_registers(address, 1, unit=1)
                value = result.registers[0] if not result.isError() else None
            elif register_type == 'coil':
                result = await client.read_coils(address, 1, unit=1)
                value = result.bits[0] if not result.isError() else None
            elif register_type == 'discrete_input':
                result = await client.read_discrete_inputs(address, 1, unit=1)
                value = result.bits[0] if not result.isError() else None

            return PointValue(
                point_id=point_id,
                value=value,
                timestamp=time.time(),
                quality='good' if not result.isError() else 'bad'
            )
        except Exception as e:
            return PointValue(
                point_id=point_id,
                value=None,
                timestamp=time.time(),
                quality='bad'
            )

    async def write_point(self, device_id: str, point_id: str, value: Any) -> bool:
        register_type, address = point_id.split(':')
        address = int(address)

        client = await self._get_client(device_id)

        try:
            if register_type == 'holding_register':
                result = await client.write_register(address, int(value), unit=1)
            elif register_type == 'coil':
                result = await client.write_coil(address, bool(value), unit=1)

            return not result.isError()
        except:
            return False

    async def _get_client(self, device_id: str) -> AsyncModbusTCPClient:
        if device_id not in self.clients:
            self.clients[device_id] = AsyncModbusTCPClient(device_id, port=self.default_port)
            await self.clients[device_id].connect()
        return self.clients[device_id]
```

#### LoRa Plugin (Device Pattern)

```python
# File: plugins/lora_plugin.py
class LoRaPlugin(DeviceProtocol):
    """LoRa protocol implementation"""

    async def read_point(self, device_id: str, point_id: str) -> PointValue:
        # LoRa addressing: device_eui, sensor_type
        # Send downlink command to request sensor reading
        await self.send_downlink(device_id, {'cmd': 'read', 'sensor': point_id})
        # Wait for uplink response (cached from last transmission)
        data = await self.get_cached_uplink(device_id, timeout=30)
        return PointValue(
            point_id=point_id,
            value=data.get(point_id),
            timestamp=data.get('timestamp'),
            quality='good' if point_id in data else 'uncertain'
        )
```

### 9.8 MQTT Implementation Example

```python
class MQTTPlugin(MessageProtocol):
    """MQTT protocol implementation"""

    def __init__(self):
        self.client = None
        self.subscriptions = {}

    async def initialize(self, config: Dict[str, Any]) -> None:
        import paho.mqtt.client as mqtt

        self.client = mqtt.Client()
        self.client.username_pw_set(
            config.get('username'),
            config.get('password')
        )

        await self.client.connect(
            config.get('broker_host', 'localhost'),
            config.get('broker_port', 1883)
        )

    async def publish(self, topic: str, payload: Any,
                     qos: int = 0, retain: bool = False) -> bool:
        result = self.client.publish(topic, json.dumps(payload), qos, retain)
        return result.rc == 0

    async def poll_topic(self, topic: str) -> Optional[TopicMessage]:
        # For MQTT, poll retained messages or recent message cache
        if topic in self.message_cache:
            return self.message_cache[topic]
        return None

    async def poll_multiple_topics(self, topics: List[str]) -> List[TopicMessage]:
        results = []
        for topic in topics:
            msg = await self.poll_topic(topic)
            if msg:
                results.append(msg)
        return results
```

### 9.9 Plugin Registration and Loading

```python
class ProtocolPluginManager:
    """Manages protocol plugin loading and registration"""

    def __init__(self):
        self.device_protocols: Dict[str, DeviceProtocol] = {}
        self.message_protocols: Dict[str, MessageProtocol] = {}
        self.service_protocols: Dict[str, ServiceProtocol] = {}
        self.load_builtin_protocols()

    def load_builtin_protocols(self):
        """Load built-in protocol implementations"""
        self.register_protocol('bacnet', BACnetPlugin())

    def register_protocol(self, name: str, plugin: ProtocolPlugin):
        """Register a protocol plugin in the appropriate category"""
        pattern = plugin.get_pattern()

        if pattern == ProtocolPattern.DEVICE_POINT:
            self.device_protocols[name] = plugin
        elif pattern == ProtocolPattern.MESSAGE_TOPIC:
            self.message_protocols[name] = plugin
        elif pattern == ProtocolPattern.SERVICE_API:
            self.service_protocols[name] = plugin

    def load_plugin(self, plugin_path: str):
        """Dynamically load a protocol plugin from file"""
        spec = importlib.util.spec_from_file_location("protocol_plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find and instantiate ProtocolPlugin subclasses
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, ProtocolPlugin) and
                obj != ProtocolPlugin):
                plugin = obj()
                self.register_protocol(name.lower().replace('plugin', ''), plugin)

    def get_device_protocol(self, name: str) -> Optional[DeviceProtocol]:
        return self.device_protocols.get(name)

    def get_message_protocol(self, name: str) -> Optional[MessageProtocol]:
        return self.message_protocols.get(name)

    def get_service_protocol(self, name: str) -> Optional[ServiceProtocol]:
        return self.service_protocols.get(name)
```

### 9.10 Unified Node Implementation

Nodes in flows use logical data sources that map to different protocol patterns:

Flow nodes work with abstract points rather than protocol-specific addresses:

```python
# In generated Python code - unified data source abstraction
async def read_data_source(source_ref: str):
    """Read from any type of data source"""
    protocol_type, source_config = parse_data_source(source_ref)

    if protocol_type == 'device':
        # Device/Point pattern (BACnet, LoRa)
        device_id, point_id = source_config['device'], source_config['point']
        protocol = plugin_manager.get_device_protocol(source_config['protocol'])
        value = await protocol.read_point(device_id, point_id)
        return value.value

    elif protocol_type == 'topic':
        # Topic pattern (MQTT) - use last retained value
        topic = source_config['topic']
        protocol = plugin_manager.get_message_protocol(source_config['protocol'])
        message = await protocol.get_retained_message(topic)
        return message.payload if message else None

    elif protocol_type == 'service':
        # Service pattern (HTTP API)
        endpoint = source_config['endpoint']
        protocol = plugin_manager.get_service_protocol(source_config['protocol'])
        response = await protocol.call_endpoint(endpoint, source_config.get('params', {}))
        return response.body

async def write_data_sink(sink_ref: str, value: Any):
    """Write to any type of data sink"""
    protocol_type, sink_config = parse_data_sink(sink_ref)

    if protocol_type == 'device':
        # Device/Point pattern
        device_id, point_id = sink_config['device'], sink_config['point']
        protocol = plugin_manager.get_device_protocol(sink_config['protocol'])
        return await protocol.write_point(device_id, point_id, value)

    elif protocol_type == 'topic':
        # Topic pattern
        topic = sink_config['topic']
        protocol = plugin_manager.get_message_protocol(sink_config['protocol'])
        return await protocol.publish(topic, value)

    elif protocol_type == 'service':
        # Service pattern
        endpoint = sink_config['endpoint']
        protocol = plugin_manager.get_service_protocol(sink_config['protocol'])
        request = ServiceRequest(
            endpoint=endpoint,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=value
        )
        response = await protocol.request(request)
        return response.status_code < 400
```

### 9.11 Example Protocol Implementations

#### LoRa Plugin (Device Pattern)

```python
# File: plugins/lora_plugin.py
class LoRaPlugin(DeviceProtocol):
    """LoRa protocol implementation"""

    async def initialize(self, config: Dict[str, Any]) -> None:
        self.gateway_url = config['gateway_url']
        self.app_key = config['app_key']
        # Initialize LoRa gateway connection

    async def discover_devices(self, timeout: int = 30) -> List[DeviceInfo]:
        # Query LoRa gateway for registered devices
        response = await self.gateway_client.get('/devices')
        return [DeviceInfo(
            device_id=device['eui'],
            name=device['name'],
            ip_address=None,  # LoRa doesn't use IP
            metadata={'rssi': device['rssi'], 'battery': device['battery']}
        ) for device in response.devices]

    async def read_point(self, device_id: str, point_id: str) -> PointValue:
        # Send downlink command to request sensor reading
        await self.send_downlink(device_id, {'cmd': 'read', 'sensor': point_id})
        # Wait for uplink response (cached from last transmission)
        data = await self.get_cached_uplink(device_id, timeout=30)
        return PointValue(
            point_id=point_id,
            value=data.get(point_id),
            timestamp=data.get('timestamp'),
            quality='good' if point_id in data else 'uncertain'
        )
```

#### MQTT Plugin (Message Pattern)

```python
# File: plugins/mqtt_plugin.py
class MQTTPlugin(MessageProtocol):
    async def initialize(self, config: Dict[str, Any]) -> None:
        # Standard MQTT client setup
        pass

    # MQTT doesn't discover "devices" - it works with topics
    # The plugin manager handles pattern differences
```

#### Adding New Protocols

```python
# Simply drop plugin file in plugins/ directory
plugin_manager.load_plugin('plugins/lora_plugin.py')
plugin_manager.load_plugin('plugins/mqtt_plugin.py')

# System automatically categorizes by pattern type
```

## 10. API Design

### 10.1 BMS Designer API Routes (Next.js - Port 3000)

#### Project Management (Local SQLite)

```
GET    /api/projects           List all projects
POST   /api/projects           Create new project
GET    /api/projects/[id]      Get project details
PUT    /api/projects/[id]      Update project
DELETE /api/projects/[id]      Delete project
POST   /api/projects/[id]/deploy  Deploy project directly to IoT Supervisor device
```

#### Flow Configuration

```
GET    /api/projects/[id]/flows List project flows
POST   /api/projects/[id]/flows Create new flow
GET    /api/flows/[id]         Get flow details
PUT    /api/flows/[id]         Update flow
DELETE /api/flows/[id]         Delete flow
```

#### Configuration Generation

```
POST   /api/config/generate    Generate JSON from flow (Zod validation)
POST   /api/config/validate    Validate configuration
```

#### IoT Supervisor Proxy (Forward to IoT Supervisor:8080)

```
GET    /api/runtime/[...path]  Dynamic proxy to IoT Supervisor API
POST   /api/runtime/[...path]  Dynamic proxy to IoT Supervisor API
```

### 10.2 BMS IoT Supervisor API (FastAPI - Port 8080) - Single BACnet Authority

#### BACnet Device Operations

```
GET    /api/devices             Discover/list BACnet devices
POST   /api/devices/discover    Trigger device discovery
GET    /api/devices/{id}        Get device details and objects
GET    /api/devices/{id}/objects Get all objects for device
POST   /api/points/read         Batch read BACnet points
POST   /api/points/write        Batch write BACnet points
GET    /api/points/live         Get live values for points
```

#### Configuration Management

```
POST   /api/config/deploy       Deploy new configuration
GET    /api/config/current      Get current loaded configuration
POST   /api/config/validate     Validate configuration structure
POST   /api/config/reload       Reload configuration from deployment
```

#### Execution Control

```
GET    /api/execution/status    IoT Supervisor health and execution status
POST   /api/execution/start     Start flow execution
POST   /api/execution/stop      Stop flow execution
POST   /api/execution/restart   Restart flow execution
GET    /api/execution/state     Real-time execution state
GET    /api/execution/logs      Execution and error logs
```

#### Data & Monitoring

```
GET    /api/data/timeseries     Historical data (24hr window)
GET    /api/data/latest         Latest values for all monitored points
GET    /api/monitoring/metrics  Performance and system metrics
GET    /api/health              IoT Supervisor health check
```

### 10.3 API Communication Flow

```
Next.js UI ←── HTTP REST ──→ IoT Supervisor API ←── BACnet ──→ Devices
     │                            │
     ▼                            ▼
SQLite (projects)           SQLite (runtime)
```

**Communication Pattern**:

1. **Designer → IoT Supervisor**: All device operations via HTTP REST
2. **IoT Supervisor → BACnet**: Exclusive protocol communication
3. **No Direct Path**: Designer never talks to BACnet directly
4. **Polling**: Designer polls IoT Supervisor for real-time updates

## 11. Implementation Roadmap

### Phase 1: Foundation ✅ **COMPLETED** (2025-09-03)

**Goal**: Complete foundational setup for 2-app architecture with shared schemas

### Phase 1a: Monorepo & Infrastructure Setup

- [x] Setup PNPM monorepo structure with workspace configuration
- [x] Create root package.json with workspace definitions
- [x] Configure pnpm-workspace.yaml and .npmrc
- [x] Setup apps/ and packages/ directory structure

### Phase 1b: Apps Foundation

**Designer App (apps/designer)**:

- [x] Initialize Next.js 15.5 with TypeScript and App Router
- [x] Setup package.json with core dependencies (React Flow, Zustand, shadcn/ui, Tailwind, better-sqlite3)
- [x] Configure basic app structure with placeholder pages and routing
- [x] Setup Jest/Vitest testing framework
- [x] Verify app starts correctly on port 3000

**IoT Supervisor App (apps/iot-supervisor-app)**:

- [x] Initialize FastAPI app with pyproject.toml
- [x] Add dependencies: BAC0==2025.06.10, bacpypes>=0.19.0, httpx==0.25.2, paho-mqtt>=2.1.0, pydantic==2.5.3, rich>=14.0.0, trio==0.30.0, typer>=0.9.0, sqlmodel>=0.0.8, loguru==0.7.3
- [x] Setup main.py with FastAPI app and CLI entry points (using Typer for commandline startup)
- [x] Configure Pytest testing framework
- [x] Verify app starts correctly on port 8080 with CLI interface

**Simulator App (apps/simulator)**:

- [x] We will keep this folder empty for now and port it to public repo when we are ready.

### Phase 1c: Shared Schema Package & Integration

- [x] Create packages/bms-schemas/ package structure
- [x] Define initial Zod Schema definitions (multi-file: position, node types, flow nodes) with versioning
- [x] Implement generation scripts (Zod → JSON Schema → Pydantic) using tsx for direct TypeScript imports
- [x] Setup comprehensive Jest testing (43 tests) with individual .spec.ts files for each schema
- [x] Integrate generated schemas in Designer app
- [x] Integrate generated schemas in IoT Supervisor app
- [x] Setup PNPM workspace build commands for schema generation
- [x] Create integration tests and e2e verification
- [x] Verify schema generation pipeline works end-to-end with multi-file organization

**Deliverables** ✅ **COMPLETED**:

- ✅ PNPM monorepo with 3 apps (Designer, IoT Supervisor, Simulator) + shared schemas
- ✅ Next.js 15.5 web-based foundation with React Flow, Zustand, Tailwind CSS v4
- ✅ Shared schema package with Zod-first validation pipeline (multi-file organization + versioning + 43 Jest tests)
- ✅ 2-tier communication architecture (Designer → IoT Supervisor API) with CORS configured
- ✅ Headless FastAPI runtime with Typer CLI interface (start-serve, start-execution, start-all commands)
- ✅ Independent BACnet simulator app directory structure (empty, ready for future)
- ✅ Complete documentation (root README.md) with development workflow and manual verification steps

**Enhanced Implementation Notes**:

- Schema package uses Zod → JSON Schema → Pydantic pipeline with tsx for direct TypeScript imports
- Designer app runs on port 3000 with schema integration test component
- IoT Supervisor app runs on port 8080/8081 with schema validation endpoints
- All apps tested and verified to work with shared schema package
- Comprehensive testing: 43 schema tests + app-specific test suites

### Phase 2: BMS Designer Development

**Goal**: Complete visual flow editor with JSON generation (Designer focus with IoT Supervisor mocks)

**Designer Tasks**:

- [ ] Implement React Flow editor with minimal node library (2-3 nodes per type: Input, Logic, Control, Output)
- [ ] Build visual flow creation and editing interface
- [ ] Implement JSON configuration generation from visual flows
- [ ] Create project management UI (create, save, load, delete projects)
- [ ] Add flow validation using generated Zod schemas
- [ ] Build device configuration UI (IoT Supervisor IP:Port settings)
- [ ] Create deployment UI with mock responses

**Mocking Requirements**:

- [ ] Create IoT Supervisor API mocks for deployment endpoint (/api/config/deploy)
- [ ] Mock device status and health check responses
- [ ] Mock deployment success/failure responses

**Deliverables**:

- Complete Designer UI with minimal node library
- JSON configuration generation from visual flows
- Project management and device configuration
- IoT Supervisor API mocking for independent development

### Phase 3: IoT Supervisor Development

**Goal**: JSON config consumption and BACnet device interaction (IoT Supervisor focus with Designer mocks)

**IoT Supervisor Tasks**:

- [ ] Port Simulator app from the bms-apps private repo to public repo.
- [ ] Implement configuration API endpoint (POST /api/config/deploy)
- [ ] Build JSON configuration interpreter for minimal node types (Input, Logic, Control, Output)
- [ ] Implement built-in BACnet client with BAC0/bacpypes
- [ ] Create device discovery and management services
- [ ] Implement flow execution engine with APScheduler (for minimal nodes)
- [ ] Add SQLite persistence for configs and device cache
- [ ] Build health/status and monitoring API endpoints
- [ ] Create CLI startup interface with Typer

**Mocking Requirements**:

- [ ] Mock Designer configuration payloads for testing
- [ ] Test against BACnet simulator for device interaction

**Deliverables**:

- Complete IoT Supervisor with minimal node execution
- BACnet device discovery and management
- Configuration persistence and CLI interface
- API endpoints for Designer integration

### Phase 4: Integration & Real Communication

**Goal**: Remove all mocks and establish real Designer ↔ IoT Supervisor communication

**Integration Tasks**:

- [ ] Replace Designer mocks with real IoT Supervisor API calls
- [ ] Replace IoT Supervisor mocks with real configuration processing
- [ ] Implement real-time polling between Designer and IoT Supervisor
- [ ] Add comprehensive error handling and retry logic for API communication
- [ ] Create end-to-end testing with complete data flow
- [ ] Verify deployment and monitoring workflows work end-to-end
- [ ] Add integration testing between Designer and IoT Supervisor

**Deliverables**:

- Complete 2-tier architecture with real communication
- End-to-end deployment pipeline working
- Real-time monitoring and visualization
- Comprehensive integration testing

### Phase 5: Complete Node Library Implementation

**Goal**: Implement remaining BMS node types for full functionality

**Node Library Tasks**:

- [ ] Add remaining Input node types (sensors, meters, manual inputs, external data)
- [ ] Add remaining Logic node types (comparisons, calculations, conditions, timers)
- [ ] Add remaining Control node types (PID controllers, schedules, sequences, loops)
- [ ] Add remaining Output node types (actuators, alarms, reports, notifications)
- [ ] Update JSON schema generation for all node types
- [ ] Update IoT Supervisor execution engine for all node types
- [ ] Create comprehensive node library documentation and examples
- [ ] Add advanced flow patterns (error handling, complex logic)

**Deliverables**:

- Complete BMS node library with 20+ node types
- Advanced flow execution capabilities
- Comprehensive documentation and examples
- Industry-standard sequences
- Complete integrator toolkit

## 12. Technology Stack Decisions

### 12.1 BMS Designer Stack (Next.js Standalone)

| Technology                | Choice               | Justification                                               |
| ------------------------- | -------------------- | ----------------------------------------------------------- |
| **Framework**             | **Next.js 15.5**     | **Standalone full-stack, App Router, API routes**           |
| **Language**              | **TypeScript**       | **Type safety, better IDE support, reduces runtime errors** |
| **Visual Programming**    | **React Flow**       | **Purpose-built for node editors, excellent performance**   |
| **State Management**      | **Zustand**          | **Lightweight, TypeScript-first state management**          |
| **UI Components**         | **shadcn/ui**        | **Modern, customizable components built on Tailwind**       |
| **Styling**               | **Tailwind CSS**     | **Utility-first, consistent design system**                 |
| **Database**              | **better-sqlite3**   | **Projects and configurations (local storage)**             |
| **Validation**            | **Generated Zod**    | **Generated from shared JSON Schema package**               |
| **IoT Supervisor Client** | **HTTP fetch**       | **Simple REST client for IoT Supervisor API**               |
| **Build Tool**            | **Next.js built-in** | **Optimized builds, hot reload, TypeScript support**        |
| **Package Manager**       | **PNPM**             | **Workspace support, efficient storage, fast installs**     |
| **Testing**               | **Jest + Vitest**    | **Frontend unit and integration testing**                   |

### 12.2 BMS IoT Supervisor Stack (Single BACnet Authority)

| Technology            | Choice                      | Justification                                           |
| --------------------- | --------------------------- | ------------------------------------------------------- |
| **Language**          | **Python 3.11+**            | **Excellent IoT libraries, async support, lightweight** |
| **API Framework**     | **FastAPI**                 | **High-performance REST API for all operations**        |
| **BACnet Operations** | **Built-in client**         | **Exclusive BACnet protocol communication**             |
| **Device Management** | **Custom service layer**    | **Device discovery, caching, polling management**       |
| **Configuration**     | **Generated Pydantic**      | **Generated from shared JSON Schema package**           |
| **Task Scheduling**   | **APScheduler**             | **Lightweight, async support, cron expressions**        |
| **Local Storage**     | **SQLite**                  | **Device cache, execution state, time-series data**     |
| **Protocol Plugins**  | **Plugin architecture**     | **Future Modbus, OPC-UA support**                       |
| **Testing**           | **Pytest**                  | **Comprehensive backend and protocol testing**          |
| **NO UI Components**  | **Pure headless execution** | **All UI handled by Designer**                          |

### 12.3 Shared Schema Package Stack

| Technology          | Choice                  | Justification                             |
| ------------------- | ----------------------- | ----------------------------------------- |
| **Schema Format**   | **JSON Schema**         | **Single source of truth for validation** |
| **TypeScript Gen**  | **Custom scripts**      | **JSON Schema → Zod + TypeScript types**  |
| **Python Gen**      | **Custom scripts**      | **JSON Schema → Pydantic models**         |
| **Package Manager** | **PNPM**                | **Workspace support for monorepo**        |
| **Build Tool**      | **TypeScript + Python** | **Cross-language code generation**        |

### 12.4 BACnet Simulator Stack

| Technology        | Choice         | Justification                            |
| ----------------- | -------------- | ---------------------------------------- |
| Language          | Python 3.11+   | Same as IoT app for consistency          |
| BACnet Library    | bacpypes3      | Real protocol implementation, not mocked |
| Web Interface     | Flask          | Lightweight for simulation monitoring    |
| Device Simulation | JSON Config    | Flexible device definitions, hot reload  |
| Development Tool  | Standalone app | Isolated from production code            |

### 12.4 Infrastructure

| Component         | Choice              | Justification                              |
| ----------------- | ------------------- | ------------------------------------------ |
| Container         | Docker              | Consistent environments, easy deployment   |
| Deployment Method | Direct API calls    | Simple HTTP deployment, no complex tooling |
| Device OS         | Any Linux           | Docker support is the only requirement     |
| Storage           | SQLite              | Local storage for both apps                |
| Logging           | File-based + SQLite | Simple logging for debugging               |
| CI/CD             | GitHub Actions      | Integrated with repo, free for open source |

## 13. Extensibility and Future Development

### 13.1 Configuration vs Code Generation Approach

The architecture uses a **configuration-first approach** with built-in extensibility:

**Current Implementation**:

- React Flow generates JSON configuration files
- Python IoT app interprets and executes configurations
- Standard node types handle common BMS operations
- Configuration schema ensures type safety and validation

**Future Extensibility Options**:

1. **Custom Python Script Nodes**:

   ```json
   {
     "type": "python_script",
     "config": {
       "script": "def process(inputs): return custom_logic(inputs)",
       "timeout_ms": 5000,
       "sandbox": true
     }
   }
   ```

2. **External Function Calls**:

   ```json
   {
     "type": "external_function",
     "config": {
       "module": "custom_modules.hvac_logic",
       "function": "calculate_setpoint",
       "parameters": { "zone": "input.zone_id" }
     }
   }
   ```

3. **Plugin Protocol Extensions**:

   - New protocol plugins follow established patterns
   - Device/Point pattern for traditional field devices
   - Message/Topic pattern for IoT protocols
   - Service/API pattern for cloud integrations

**Benefits of Configuration Approach**:

- **Hot Reload**: Configuration changes apply immediately without redeployment
- **Validation**: JSON Schema prevents runtime errors
- **Debugging**: Clear separation between flow logic and execution
- **Security**: Sandboxed execution environment for custom scripts
- **Maintenance**: No generated code to manage or version

## 14. Security Considerations [WIP]

### 14.1 Authentication & Authorization

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
  - Admin: Full system access
  - Operator: Create/modify flows, view data
  - Viewer: Read-only access
- Multi-factor authentication for admin accounts
- Session timeout after inactivity

### 14.2 Code Execution Security

- Sandboxed Python execution environment
- Whitelist of allowed Python modules
- Resource limits (CPU, memory, execution time)
- Input validation and sanitization
- No direct file system access from generated code
- Audit logging of all executions

### 14.3 Communication Security

- TLS 1.3 for all API communications
- HTTPS for polling-based data access
- Certificate pinning for IoT to frontend communication
- API rate limiting and DDoS protection
- Request signing for critical operations

### 14.4 Data Security

- Encryption at rest for sensitive configuration
- Encryption in transit for all data
- Secure credential storage (HashiCorp Vault)
- Regular security audits
- Compliance with industrial standards (ISA-95, IEC 62443)

## 15. Deployment Architecture [WIP]

### 15.1 Development Environment

```
Local Development:
- Frontend Dev Server (Port 3000)
- IoT App in Docker (Port 8000 + 8080)
- SQLite (embedded)
- BACnet Simulator
```

### 15.2 Production Deployment with Balena.io

```
┌─────────────────────────────────────────┐
│     Developer Machine                   │
│  ┌─────────────────────────────────┐   │
│  │ Desktop App (Electron)          │   │
│  │ - Creates flows                 │   │
│  │ - Generates Python code         │   │
│  └────────────┬────────────────────┘   │
└───────────────┼─────────────────────────┘
                │ Push via Balena API
                ▼
┌─────────────────────────────────────────┐
│         Balena.io Cloud                 │
│  ┌─────────────────────────────────┐   │
│  │ Fleet Management                │   │
│  │ - Container Registry            │   │
│  │ - Device Configuration          │   │
│  │ - OTA Updates                   │   │
│  └────────────┬────────────────────┘   │
└───────────────┼─────────────────────────┘
                │ Deploy Containers
                ▼
┌─────────────────────────────────────────┐
│     IoT Devices (Raspberry Pi, etc.)    │
│  ┌─────────────────────────────────┐   │
│  │ BalenaOS                        │   │
│  │ ┌─────────────────────────────┐ │   │
│  │ │ IoT App Container           │ │   │
│  │ │ - Python Execution Engine   │ │   │
│  │ │ - BACnet/Modbus Plugins     │ │   │
│  │ │ - Web Dashboard (Port 8080) │ │   │
│  │ │ - SQLite Storage            │ │   │
│  │ └─────────────────────────────┘ │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Balena.io Benefits**:

- Zero-touch provisioning
- Secure remote access
- Container-based deployment
- Multi-architecture support (ARM, x86)
- Fleet-wide updates
- Device monitoring and logs
- Environment variable management

#### Multi-Site Deployment

```
Site A                     Central Management
┌──────────────┐          ┌──────────────────┐
│ Local IoT    │◄─────────┤ Central Dashboard│
└──────┬───────┘          └──────────────────┘
       ▼                            ▲
┌──────────────┐                    │
│ BMS Devices  │                    │
└──────────────┘                    │
                                    │
Site B                              │
┌──────────────┐                    │
│ Local IoT    │◄───────────────────┘
└──────┬───────┘
       ▼
┌──────────────┐
│ BMS Devices  │
└──────────────┘
```

### 15.3 Balena.io Deployment Benefits

**For BMS Integrators**:

- **Remote Deployment**: Push code to devices anywhere in the world
- **Fleet Management**: Organize devices by building/customer
- **OTA Updates**: Update control logic without site visits
- **Device Monitoring**: See device status in Balena dashboard
- **Rollback**: Instantly revert to previous working version
- **Environment Config**: Set device-specific parameters remotely

**Scaling Model**:

- Each building/site has its own Balena fleet
- Devices scale independently within each fleet
- Desktop app manages multiple fleets simultaneously
- No centralized infrastructure needed

**Performance Targets**:

- 50+ BMS devices per IoT device (Raspberry Pi 4)
- Sub-second flow deployment via Balena
- 24hr local data retention per device
- Web dashboard responsive under 2 seconds

## 16. Debug and Testing Features

### 16.1 Debug Data Collection

- 15-minute rolling window of flow execution data
- Device communication logs
- Flow execution traces
- Performance metrics for optimization

### 16.2 Testing Tools for Integrators

- Device simulators for all protocols
- Flow step-through debugger
- Breakpoint support in visual flows
- Data injection for testing scenarios

### 16.3 Commissioning Support

- Automated test sequence execution
- Commissioning report generation
- Device communication verification
- Performance baseline capture

## 17. Testing Strategy

### 17.1 Unit Testing

- Frontend: Component testing with React Testing Library
- Backend: Function testing with Pytest
- Code generation: AST validation tests
- Protocol adapters: Mock device testing

### 17.2 Integration Testing

- API endpoint testing
- HTTP polling performance testing
- Flow deployment pipeline testing
- Device communication testing

### 17.3 End-to-End Testing

- Complete flow creation to execution
- Multi-device scenarios
- Failure recovery testing
- Performance testing under load

### 17.4 Testing Environments

- Local: Docker Compose with simulators
- Staging: Replica of production
- Production: Canary deployments

## 18. Documentation Requirements

### 18.1 Technical Documentation

- API documentation (auto-generated from OpenAPI)
- Code generation specification
- Protocol implementation guides
- Deployment procedures

### 18.2 User Documentation

- Getting started guide
- Flow editor tutorial
- Node reference manual
- Troubleshooting guide

### 18.3 Developer Documentation

- Architecture overview (this document)
- Contributing guidelines
- Development setup
- Plugin development guide

## 19. Risk Analysis and Mitigation

| Risk                                      | Impact | Probability | Mitigation                               |
| ----------------------------------------- | ------ | ----------- | ---------------------------------------- |
| Generated code has security vulnerability | High   | Medium      | Sandboxing, code review, static analysis |
| Device communication failure              | High   | Medium      | Retry logic, fallback values, alerts     |
| Performance degradation with scale        | Medium | High        | Load testing, optimization, caching      |
| Complex flows difficult to debug          | Medium | Medium      | Visual debugger, step-through execution  |
| Protocol compatibility issues             | Medium | Medium      | Extensive testing, protocol validation   |
| Data loss during system failure           | High   | Low         | Regular backups, transaction logs        |

## 20. Future Enhancements

### Near-term (6-12 months)

- Integration with existing BMS platforms
- Cloud-based flow repository for teams
- Additional protocol plugins (LoRa, MQTT, Zigbee, KNX)
- Industry-specific flow template libraries
- Remote deployment capabilities

### Long-term (12-24 months)

- AI-assisted flow creation from specifications
- Automatic code optimization suggestions
- Integration with BIM models
- Compliance checking (ASHRAE, energy codes)
- Multi-vendor device abstraction layer

## 21. Conclusion

The BMS Supervisor Controller architecture delivers a comprehensive 4-application system with 3-tier communication that revolutionizes visual BMS programming. By consolidating UI in the Designer while maintaining clean separation with the headless IoT Supervisor, we achieve both sophisticated user experience and reliable IoT operation.

**Key Architectural Innovations**:

- **3-Tier Architecture**: Next.js → Designer FastAPI → IoT Supervisor FastAPI enables clean separation with unified UI
- **UI Consolidation**: Single sophisticated interface for both design and real-time monitoring
- **JSON Configuration**: Configuration-driven approach with compile-time validation ensures reliability
- **Direct API Deployment**: Streamlined configuration deployment via HTTP REST APIs
- **Real-time Execution Visualization**: Live flow execution tracking through API polling
- **Independent Operation**: IoT Supervisor operates autonomously with its own database from deployment package
- **Multi-pattern Protocol Support**: Extensible plugin architecture for BACnet, Modbus, MQTT, and future protocols

**Technical Excellence**:

- **Modern Web Stack**: Next.js + TypeScript + Tailwind for professional UI experience
- **High-Performance APIs**: FastAPI backends optimized for both development and IoT deployment
- **Deployment Flexibility**: Support for Balena.io, Docker, and direct API deployment
- **Development Workflow**: Integrated BACnet simulator with hot-reload capabilities
- **Security & Validation**: Compile-time configuration validation with comprehensive testing

This architecture positions the BMS Supervisor Controller as the definitive tool for BMS integrators, dramatically reducing commissioning time through visual programming while providing enterprise-grade monitoring and deployment capabilities. The combination of intuitive design tools, real-time execution visualization, and flexible deployment options makes complex BMS integration accessible to technical integrators without sacrificing professional reliability or performance.

## 22. Architecture Assessment

### 22.1 Review Process

This architecture underwent comprehensive review to identify potential weaknesses and validate design decisions. The assessment process examined system design, scalability, security, reliability, and overall architectural quality.

### 22.2 Initial Concerns and Clarifications

**Initial Rating: 4/10** - Based on several misconceptions about the architecture scope and implementation details.

#### Concern 1: Over-Engineering (Resolved)

**Initial Assessment**: "4 separate applications creates excessive complexity"
**Clarification**:

- 2 applications total: Designer, IoT Supervisor
- Simulator is development-only tool (appropriate separation)
- Direct API deployment eliminates CLI complexity
  **Resolution**: Simplified 2-app architecture with direct deployment

#### Concern 2: Communication Latency (Resolved)

**Initial Assessment**: "Multi-tier polling creates latency concerns"
**Clarification**:

- All components deployed on same IoT device (localhost communication)
- No cross-network polling latency
- Same-machine HTTP communication is sub-millisecond
  **Resolution**: Polling performance acceptable for local communication

#### Concern 3: Resource Consumption (Resolved)

**Initial Assessment**: "Next.js on IoT devices wastes resources"
**Clarification**:

- Designer UI runs on-demand only when debugging/configuration needed
- IoT Supervisor-only mode for production deployment (no UI overhead)
- Modern IoT devices (8-16GB) easily handle full stack when required
  **Resolution**: No resource waste, flexible deployment based on operational needs

#### Concern 4: Project Scope (Resolved)

**Initial Assessment**: "Missing industrial HMI and monitoring requirements"
**Clarification**:

- Operational monitoring handled by separate application
- This project focuses on visual programming and execution only
- Scope appropriately constrained to development/deployment workflow
  **Resolution**: Clear project boundaries eliminate scope creep concerns

#### Concern 5: Data Synchronization (Resolved)

**Initial Assessment**: "Dual SQLite databases create synchronization complexity"
**Clarification**:

- Designer is single source of truth for all configuration
- Unidirectional data flow: Designer → IoT Supervisor (consume only)
- No bidirectional synchronization required
  **Resolution**: Simple, reliable data architecture with clear ownership

### 22.3 Remaining Considerations

**Minor Optimization Opportunities**:

1. **BACnet Protocol Efficiency**

   - Current polling strategy could benefit from COV (Change of Value) subscriptions
   - Implementation detail for built-in BACnet client optimization
   - Impact: Network efficiency improvement, not architectural concern

2. **Schema Pipeline Coordination**

   - Pydantic → JSON Schema → TypeScript type generation requires build coordination
   - Impact: Development workflow consideration, not runtime issue

### 22.4 Architectural Strengths

**Design Excellence**:

- **Clean Separation**: Designer handles UI/configuration, IoT Supervisor handles execution
- **Unidirectional Data Flow**: Single source of truth eliminates sync complexity
- **Extensible Foundation**: Plugin architecture supports future protocol additions
- **Resource Efficiency**: On-demand UI deployment with runtime-only production mode
- **Modern Stack**: Next.js + FastAPI + Pydantic provides excellent developer experience

**Operational Benefits**:

- **Deployment Flexibility**: Direct API deployment supports multiple target platforms
- **Development Workflow**: Integrated simulator with hot-reload capabilities
- **Schema Validation**: Pydantic-centered approach ensures configuration integrity
- **Protocol Abstraction**: Multi-pattern plugin design accommodates diverse BMS protocols

### 22.5 Extensibility Assessment

The architecture provides excellent extensibility foundations:

**Communication Layer**: HTTP polling can be upgraded to WebSockets for real-time communication without architectural changes

**Protocol Support**: Plugin architecture accommodates future protocols (MQTT, LoRa, KNX) through established patterns

**Deployment Targets**: Direct API approach enables support for additional platforms (AWS IoT, Azure IoT Edge) without core changes

**Execution Engine**: Configuration-driven approach allows new node types and control logic without runtime modifications

### 22.6 Final Assessment

**Overall Rating: 9/10**

This architecture effectively addresses the core problem of visual BMS programming for integrators with:

- Appropriate technology choices for each component
- Clean separation of design-time vs runtime concerns
- Unidirectional data flow eliminating complexity
- Resource-efficient deployment strategies
- Strong foundation for future enhancements

**Recommendation**: Proceed with implementation. The architecture is well-suited for the intended scope and provides excellent extensibility for future requirements.

**Minor Optimization**: Consider BACnet COV subscriptions in the shared client package for improved network efficiency, but this is an implementation detail rather than an architectural requirement.
