# Designer MQTT Integration Specification

## Requirements

### Core Requirements

1. **MQTT.js Library**: Add MQTT.js to Designer app for WebSocket-based MQTT communication
2. **WebSocket Connection**: Connect to `wss://<host>/mqtt` (reverse proxy), NOT `ws://localhost:8083`
3. **MQTT 5.0 Request/Response Pattern**: Implement proper MQTT 5 request/response with correlation IDs, Response Topic, and configurable timeouts
4. **Connection Management**: Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, 16s, 30s max)
5. **UI Indicators**: Show MQTT connection status and broker health from retained status messages
6. **Topic Configuration**: Use existing mqtt-topics package for consistent topic structure - leverage ALL topics defined there
7. **BACnet Node Updates**: Nodes must receive real-time property updates via MQTT
8. **Single Source of Truth**: BACnet nodes own their data and subscription lifecycle

### MQTT 5.0 Request/Response Requirements

- **Correlation Data**: Use MQTT 5.0 correlation data property for request/response matching
- **Response Topic**: Set response topic in request message properties
- **Topic Structure**: Follow mqtt_topics package exactly - use request/response topic pairs
- **Command Support**: Support all commands defined in mqtt_topics (get_config, reboot, set_value_to_point, start_monitoring, stop_monitoring)
- **QoS Levels**: Respect QoS settings from topic configuration
- **Retain Flags**: Honor retain settings from topic configuration

### Technical Constraints

- Use pnpm as package manager
- Follow TypeScript coding standards (camelCase, explicit types, object parameters)
- Use RxJS for subscription management (keep it simple)
- Integrate with existing Zustand store architecture
- Maintain compatibility with existing DataGraph and message routing

### Functional Requirements

- **Commands**: Send commands to IoT devices using proper request/response topics
- **Real-time Updates**: Use `data/point_bulk` for point value changes and derive per-point updates client-side. `data/point` is not used currently.
- **Heartbeat Monitoring**: Track supervisor health via `status/heartbeat` topic
- **Alert Management**: Support acknowledge and resolve alert topics
- **Error Handling**: Graceful degradation on connection loss, timeout handling for requests
- **Memory Management**: Proper cleanup of subscriptions when nodes are destroyed

## Architecture Overview

### Component Hierarchy

```
Designer App
├── MQTT Bus (RxJS-based singleton)
│   ├── MqttBus (connect, request/response, domain streams)
│   └── Topics via mqtt-topics package
├── State Management (Zustand)
│   ├── MQTT slice (connection, broker health, node runtime)
│   └── flow-slice (existing, graph config)
├── BACnet Nodes (Data Layer)
│   ├── Receive injected MqttBus at creation
│   ├── Bind domain streams → MQTT slice (no notify)
│   └── Cleanup subscription on destroy
└── UI Components
    └── SupervisorsTab (connection indicators)
```

### MQTT Topics Integration

The implementation must use ALL topics from `/Users/amol/Documents/ai-projects/bms-supervisor-controller/packages/mqtt_topics/topics.json`:

```json
{
  "command": {
    "get_config": { "request": {...}, "response": {...} },
    "reboot": { "request": {...}, "response": {...} },
    "set_value_to_point": { "request": {...}, "response": {...} },
    "start_monitoring": { "request": {...}, "response": {...} },
    "stop_monitoring": { "request": {...}, "response": {...} }
  },
  "status": {
    "heartbeat": {...}
  },
  "data": {
    "point": {...},
    "point_bulk": {...}
  },
  "alert_management": {
    "acknowledge": {...},
    "resolve": {...}
  }
}
```

Note: `data.point.topic` is not implemented for now. The app MUST rely on `data.point_bulk` for real-time point updates and derive individual point values client-side via RxJS filtering.

## Detailed Design

### Updated Design: MQTT Bus Singleton (RxJS-first)

Replace the per-node subscribe and notify pattern with a single MqttBus that hides mqtt.js and exposes typed RxJS streams. Nodes receive the bus at creation and bind streams to the store. No `subscribeMqtt` and no `notifyGraphUpdate`.

#### 1. MQTT Bus (`apps/designer/src/lib/mqtt/mqtt-bus.ts`)

```typescript
import {
  BehaviorSubject,
  Observable,
  ReplaySubject,
  Subject,
  filter,
  map,
  merge,
  shareReplay,
  take,
  timeout,
  throwError,
} from "rxjs";
import { connect, MqttClient } from "mqtt";
import { v4 as uuidv4 } from "uuid";
import {
  getAllTopics,
  type AllTopics,
  type TopicParams,
  CommandNameEnum,
} from "mqtt_topics";

export type ConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

export interface MqttMessage<T = any> {
  topic: string;
  payload: T;
  correlationId?: string;
  responseTopic?: string;
}

// SupervisorConfig identifies the active supervisor context (varies per project)
// Changing this config between projects requires stopping and restarting the bus.
export interface SupervisorConfig {
  organizationId: string;
  siteId: string;
  iotDeviceId: string;
}

export class MqttBus {
  private client?: MqttClient;
  private topics?: AllTopics;
  private messages$ = new Subject<MqttMessage>();
  private connection$ = new BehaviorSubject<ConnectionStatus>("disconnected");
  private heartbeat$ = new ReplaySubject<any>(1);
  private pointBulk$ = new Subject<any>();

  private reconnectAttempts = 0;
  private readonly reconnectDelays = [1000, 2000, 4000, 8000, 16000, 30000];
  private config?: SupervisorConfig;

  readonly connectionStatus$: Observable<ConnectionStatus> =
    this.connection$.asObservable();
  readonly heartbeatStream$: Observable<any> = this.heartbeat$.asObservable();
  readonly pointBulkStream$: Observable<any> = this.pointBulk$.pipe(
    shareReplay({ bufferSize: 1, refCount: true }),
  );

  start(config: SupervisorConfig): void {
    const wasStarted = !!this.client;
    const sameConfig = JSON.stringify(this.config) === JSON.stringify(config);
    if (wasStarted && sameConfig && this.client?.connected) return;

    this.config = config;
    this.topics = this.buildTopics(config);
    this.connect();
  }

  stop(): void {
    this.client?.end(true);
    this.client = undefined;
    this.connection$.next("disconnected");
  }

  private buildTopics(config: SupervisorConfig): AllTopics {
    const params: TopicParams = {
      organization_id: config.organizationId,
      site_id: config.siteId,
      iot_device_id: config.iotDeviceId,
    };
    return getAllTopics({ params });
  }

  private connect(): void {
    if (!this.config || !this.topics) return;

    // Guard SSR; allow Node runtime via env vars
    const isBrowser = typeof window !== "undefined";
    const allowNode = !isBrowser && process?.env?.MQTT_ENABLE_SERVER === "1";
    if (!isBrowser && !allowNode) return;

    const url = isBrowser
      ? `wss://${(window as any).location.host}/mqtt`
      : (process?.env?.MQTT_URL as string) ?? "";

    if (!url) {
      throw new Error("MQTT_URL env required for Node runtime");
    }

    this.connection$.next("connecting");

    this.client = connect(url, {
      clientId: `designer_${this.config.iotDeviceId}_${Date.now()}`,
      reconnectPeriod: 0,
      connectTimeout: 30000,
      protocolVersion: 5,
      clean: true,
    });

    this.client.on("connect", () => {
      this.connection$.next("connected");
      this.reconnectAttempts = 0;
      this.subscribeCoreTopics();
    });

    this.client.on("message", (topic, payload, packet) => {
      try {
        const correlationData = packet.properties?.correlationData;
        const responseTopic = packet.properties?.responseTopic;
        const msg: MqttMessage = {
          topic,
          payload: JSON.parse(payload.toString()),
          correlationId: correlationData
            ? correlationData.toString()
            : undefined,
          responseTopic: responseTopic ? responseTopic.toString() : undefined,
        };
        this.messages$.next(msg);
        this.routeToDomainStreams(msg);
      } catch (e) {
        console.error("MQTT parse error", e);
      }
    });

    this.client.on("error", (err) => {
      console.error("MQTT error", err);
      this.connection$.next("error");
    });

    this.client.on("close", () => {
      this.connection$.next("disconnected");
      this.scheduleReconnect();
    });
  }

  private subscribeCoreTopics(): void {
    if (!this.client || !this.topics) return;
    const { status, data, command } = this.topics;
    // Fixed topics
    this.client.subscribe(status.heartbeat.topic, {
      qos: status.heartbeat.qos as 0 | 1 | 2,
    });
    this.client.subscribe(data.point_bulk.topic, {
      qos: data.point_bulk.qos as 0 | 1 | 2,
    });
    // Command response topics (subscribe once; filter by correlationId in request())
    for (const key of Object.keys(command)) {
      const resp = (command as any)[key]?.response;
      if (resp?.topic) {
        this.client.subscribe(resp.topic, { qos: resp.qos as 0 | 1 | 2 });
      }
    }
  }

  // Notes:
  // - Response Topic Subscription: response topics for all commands are subscribed once at connect
  //   (and on reconnect). request() filters replies by correlationId and does not subscribe per call.
  // - SSR/Node guard: Do not connect during Next.js SSR. In a Node runtime, set
  //   MQTT_ENABLE_SERVER=1 and MQTT_URL to enable server-side connections.

  private scheduleReconnect(): void {
    if (!this.config) return;
    const attempt = Math.min(
      this.reconnectAttempts,
      this.reconnectDelays.length - 1,
    );
    const delay = this.reconnectDelays[attempt];
    this.reconnectAttempts++;
    setTimeout(() => this.connect(), delay);
  }

  private routeToDomainStreams(msg: MqttMessage): void {
    if (!this.topics) return;
    const { status, data } = this.topics;
    if (msg.topic === status.heartbeat.topic) {
      this.heartbeat$.next(msg.payload);
    } else if (msg.topic === data.point_bulk.topic) {
      this.pointBulk$.next(msg.payload);
    }
  }

  // Field names for point_bulk payloads:
  // - Topic-scoped: iot_device_id (supervisor) — carried in the topic path
  // - Bulk-level: controller_id (BACnet controller/device)
  // - Per-point: iot_device_point_id (supervisor's point identifier)
  // Coerce IDs to strings when matching to avoid silent mismatches ("1" vs 1).
  //
  // Note: The complete point_bulk payload schema is defined in bms-iot-app.
  // Publishing this schema to a shared package is out of scope for this implementation.
  // Expected structure:
  // {
  //   controller_id: string
  //   timestamp: number
  //   points: Array<{
  //     iot_device_point_id: string
  //     present_value: number | boolean | string
  //     status_flags?: number
  //     properties?: Record<string, unknown>
  //   }>
  // }

  streamForPoint(ids: {
    controllerId: string;
    pointId: string;
  }): Observable<any> {
    if (!ids.controllerId || !ids.pointId) {
      return throwError(
        () =>
          new Error(
            `Invalid point IDs: controllerId=${ids.controllerId}, pointId=${ids.pointId}`,
          ),
      );
    }

    const fromBulk$ = this.pointBulkStream$.pipe(
      filter((b: any) => {
        if (!b?.controller_id) {
          console.warn("point_bulk message missing controller_id", b);
          return false;
        }
        return String(b.controller_id) === ids.controllerId;
      }),
      map((b: any) => {
        const point = b.points?.find(
          (x: any) => String(x?.iot_device_point_id) === ids.pointId,
        );
        if (!point) {
          console.warn(
            `Point ${ids.pointId} not found in bulk message for controller ${ids.controllerId}`,
          );
        }
        return point;
      }),
      filter((x: any) => !!x),
    );
    return fromBulk$.pipe(shareReplay({ bufferSize: 1, refCount: true }));
  }

  request<T = any>(
    command: CommandNameEnum,
    payload: any,
    timeoutMs = 30000,
  ): Observable<T> {
    if (!this.client || !this.client.connected || !this.topics) {
      throw new Error("MQTT not connected");
    }
    const correlationId = uuidv4();
    const cmd = this.topics.command[command];
    if (!cmd) throw new Error(`Unknown command ${command}`);
    const req = cmd.request;
    const res = cmd.response;

    const response$ = this.messages$.pipe(
      filter((m) => m.topic === res.topic && m.correlationId === correlationId),
      map((m) => m.payload as T),
      take(1),
      timeout({ each: timeoutMs }),
    );

    this.client.publish(req.topic, JSON.stringify(payload), {
      qos: req.qos as 0 | 1 | 2,
      retain: req.retain,
      properties: {
        correlationData: Buffer.from(correlationId),
        responseTopic: res.topic,
      },
    });

    return response$;
  }
}

let _bus: MqttBus | undefined;
export function getMqttBus(): MqttBus {
  if (!_bus) _bus = new MqttBus();
  return _bus;
}
```

#### 2. Store Integration (connection + health)

```typescript
import { StateCreator } from "zustand";
import { Subject, interval, Subscription } from "rxjs";
import { takeUntil } from "rxjs/operators";
import { getMqttBus } from "@/lib/mqtt/mqtt-bus";
import { CommandNameEnum } from "mqtt-topics";

export interface BrokerHealth {
  status: "unknown" | "healthy" | "unhealthy";
  lastHeartbeat?: number;
  uptimeSeconds?: number;
  version?: string;
}

export interface MQTTSlice {
  connectionStatus: "disconnected" | "connecting" | "connected" | "error";
  brokerHealth: BrokerHealth;
  lastError?: string;
  startMqtt: (cfg: {
    organization_id: string;
    site_id: string;
    iot_device_id: string;
  }) => void;
  stopMqtt: () => void;
  sendCommand: (command: CommandNameEnum, payload: any) => Promise<any>;
}

export const createMQTTSlice: StateCreator<MQTTSlice> = (set, get) => ({
  connectionStatus: "disconnected",
  brokerHealth: { status: "unknown" },

  startMqtt: (cfg) => {
    const bus = getMqttBus();
    bus.start({
      organizationId: cfg.organization_id,
      siteId: cfg.site_id,
      iotDeviceId: cfg.iot_device_id,
    });

    // Lifecycle gate for slice-level streams
    const stop$ = new Subject<void>();
    (get as any)._mqttStop$ = stop$;

    // Connection status
    bus.connectionStatus$
      .pipe(takeUntil(stop$))
      .subscribe((s) => set({ connectionStatus: s }));

    // Heartbeat marks healthy and records timestamp
    bus.heartbeatStream$.pipe(takeUntil(stop$)).subscribe({
      next: (hb) =>
        set({
          brokerHealth: {
            status: "healthy",
            lastHeartbeat: Date.now(),
            uptimeSeconds: hb?.uptime_seconds,
            version: hb?.version,
          },
        }),
      error: (e) =>
        set({
          brokerHealth: { ...get().brokerHealth, status: "unhealthy" },
          lastError: String(e),
        }),
    });

    // Heartbeat watchdog: downgrade to unhealthy when silence exceeds threshold (~35s)
    const HEARTBEAT_THRESHOLD_MS = 35_000;
    interval(5_000)
      .pipe(takeUntil(stop$))
      .subscribe(() => {
        const { brokerHealth } = get();
        if (!brokerHealth.lastHeartbeat) return;
        const silentFor = Date.now() - brokerHealth.lastHeartbeat;
        if (
          silentFor > HEARTBEAT_THRESHOLD_MS &&
          brokerHealth.status !== "unhealthy"
        ) {
          set({ brokerHealth: { ...brokerHealth, status: "unhealthy" } });
        }
      });
  },

  stopMqtt: () => {
    getMqttBus().stop();
    // Tear down all slice-level streams via lifecycle gate
    const stop$: Subject<void> | undefined = (get as any)._mqttStop$;
    if (stop$) {
      stop$.next();
      stop$.complete();
      (get as any)._mqttStop$ = undefined;
    }
    set({
      connectionStatus: "disconnected",
      brokerHealth: { status: "unknown" },
      lastError: undefined,
    });
  },

  sendCommand: async (command, payload) => {
    const bus = getMqttBus();
    return bus.request(command, payload).toPromise();
  },
});
```

#### 1.a Bus Lifecycle (Single Active Project)

- Single instance: Only one `MqttBus` instance is active at any time.
- Control via store: Start/stop the bus through `createMQTTSlice` actions (`startMqtt`, `stopMqtt`). The slice wraps the singleton bus and maintains connection/broker health in state.
- Start: Dispatch `startMqtt({ organization_id, site_id, iot_device_id })` when the active project's deployment config is available.
- Stop: Dispatch `stopMqtt()` on project close/switch or app teardown.
- Re-init on project change: If the active project changes, stop the bus and start it again with the new config (or call `start()` which is idempotent and will reconnect when config differs).
- Ordering: Start the bus before constructing any nodes. Nodes subscribe inside their constructors and expect the bus to be running.
- SSR/HMR: Guard for browser environment (`typeof window !== 'undefined'`) and ensure `start()` is idempotent to avoid duplicate connections during fast-refresh.

#### 1.b App Flow Integration (where to start/stop)

**Start location:** As soon as the active project's deployment config is available in the project workspace shell (before nodes are constructed), dispatch `startMqtt(...)`.

- Recommended place: the project route container, e.g., `apps/designer/src/app/projects/[id]/page.tsx` (or its layout/provider shell) where deployment config is fetched.

**Stop location:** Dispatch `stopMqtt()` when leaving the project workspace (route unmount) or when switching to a different project.

**Ordering guarantee:** Start the bus before constructing the DataGraph and node instances so constructor-based subscriptions attach to a live bus.

**Critical startup sequence to prevent race conditions:**

```typescript
// In Project Workspace shell (React), after deployment config resolves
const startMqtt = useFlowStore((s) => s.startMqtt); // from MQTT slice
const stopMqtt = useFlowStore((s) => s.stopMqtt); // from MQTT slice
const clearAllNodes = useFlowStore((s) => s.clearAllNodes); // Removes all nodes via DataGraph
const loadWorkflow = useFlowStore((s) => s.loadWorkflow); // Deserializes and constructs nodes
const connectionStatus = useFlowStore((s) => s.connectionStatus);

useEffect(() => {
  if (!cfg) return;

  // CRITICAL SEQUENCE: Ensure clean state before starting MQTT
  // Step 1: Stop any existing MQTT connection
  stopMqtt();

  // Step 2: Clear all existing nodes (this calls destroy() on each node)
  clearAllNodes();

  // Step 3: Start MQTT bus with new config
  startMqtt({
    organization_id: cfg.organization_id,
    site_id: cfg.site_id,
    iot_device_id: cfg.iot_device_id,
  });

  return () => {
    // Cleanup on unmount or config change
    clearAllNodes(); // Destroy nodes first
    stopMqtt(); // Then stop bus
  };
}, [cfg?.organization_id, cfg?.site_id, cfg?.iot_device_id]);

// Step 4: Wait for connection before loading workflow
useEffect(() => {
  if (connectionStatus === "connected" && workflowToLoad) {
    loadWorkflow(workflowToLoad); // Constructs nodes after bus is ready
  }
}, [connectionStatus, workflowToLoad]);
```

**Startup sequence rules:**

1. **Before MQTT start**: Clear all existing nodes via `clearAllNodes()` (calls `destroy()` on each)
2. **Start MQTT**: Call `startMqtt()` and wait for `connectionStatus === 'connected'`
3. **After connection**: Deserialize workflow and construct nodes (they subscribe in constructors)
4. **On teardown**: Always destroy nodes before stopping MQTT to prevent errors

**SSR/HMR considerations:**

- Ensure this effect runs in the browser only; avoid calling `start()` during SSR
- `startMqtt()` is idempotent; if the same config is passed again, it maintains the current connection
- During HMR, the cleanup function will run before re-mounting, ensuring clean reconnection

**Project switch handling:**

- React unmounts the workspace → cleanup runs → `clearAllNodes()` then `stopMqtt()`
- Next mount starts with new config → clean state → new connection → new nodes

#### 1.c React Flow Integration (node delete → destroy())

- Hook into React Flow's `onNodesDelete` to trigger node destruction via the store and DataGraph:

```typescript
// In the Flow canvas/container where React Flow is used
const removeNode = useFlowStore((s) => s.removeNode);

const handleNodesDelete = useCallback(
  (deleted) => {
    for (const n of deleted) removeNode(n.id);
  },
  [removeNode],
);

// <ReactFlow onNodesDelete={handleNodesDelete} ... />
```

Call path for deletion:

- `onNodesDelete` → `flowSlice.removeNode(id)` → `dataGraph.removeNode(id)`
- `dataGraph.removeNode(id)` must call `dataNode.destroy?.()` **before** `reset?.()` to unsubscribe MQTT streams first, then cleanup timers/intervals
- Critical: Call `destroy()` before removing edges and the node entry to prevent memory leaks from active MQTT subscriptions
- On project teardown, call `dataGraph.clear()` (or iterate and remove all nodes) to ensure `destroy()` runs for each node before `stopMqtt()`

**DataGraph.removeNode() implementation requirement:**

```typescript
removeNode(nodeId: string): void {
  const node = this.nodesMap.get(nodeId)
  if (node) {
    const dataNode = node.data as DataNode
    // CRITICAL: Call destroy() FIRST to cleanup MQTT subscriptions
    if ('destroy' in dataNode && typeof dataNode.destroy === 'function') {
      dataNode.destroy()
    }
    // Then call reset() to cleanup timers/intervals
    if ('reset' in dataNode && typeof dataNode.reset === 'function') {
      dataNode.reset()
    }
  }
  // ... rest of removal logic
}
```

Factory call signature (inject bus + nodeDidUpdate):

```typescript
// In flow slice
const bus = getMqttBus();
const dataNode = factory.createDataNodeFromBacnetConfig({
  config,
  id,
  deps: {
    bus,
    nodeDidUpdate, // defined in flow slice; see pseudocode above
  },
});
```

Deserializer integration (inject at node creation during load):

```typescript
// In workflow-serializer.ts (spec sketch)
export function createNodeFactoryWithDeps(deps: {
  bus: MqttBus;
  nodeDidUpdate: NodeDidUpdate;
}) {
  return function nodeFactory(nodeType: string, data: Record<string, unknown>) {
    switch (nodeType) {
      case "AnalogInputNode":
      case "BinaryInputNode":
      case "AnalogOutputNode":
        return factory.createDataNodeFromBacnetConfig({
          config: data.metadata as BacnetConfig,
          id: data.id as string,
          deps,
        });
      default:
        return /* existing logic */ null as any;
    }
  };
}

// Used by prepareForReactFlow(...)
const nodeFactory = createNodeFactoryWithDeps({ bus, nodeDidUpdate });
prepareForReactFlow({ versionedConfig, nodeFactory });
```

Injection points summary:

- Flow slice: addNodeFromInfrastructure → pass `{ bus, nodeDidUpdate }` to the factory.
- Deserializer: createNodeFactoryWithDeps → pass `{ bus, nodeDidUpdate }` so loaded nodes are constructed with the same dependencies.

Runtime update callback wiring (choose one and keep consistent):

- DataGraph receives a `nodeDidUpdate(nodeId, patch)` function from the store and passes it to node constructors via the factory. Nodes call it to write runtime patches. DataGraph does not perform any store writes itself.
- Or, the store passes the `updateRuntime` function directly to the node factory without DataGraph involvement beyond node construction.

#### 3. BACnet Node Binding (constructor/destroy, callback-based, no notify)

```typescript
import type { Subscription } from "rxjs";
import type { MqttBus } from "@/lib/mqtt/mqtt-bus";

// Inject a single callback to write runtime patches; keeps nodes decoupled from the store
type NodeDidUpdate = (nodeId: string, patch: Record<string, unknown>) => void;

export class BinaryInputNode {
  private sub?: Subscription;
  constructor(
    private readonly id: string,
    private readonly controllerId: string,
    private readonly pointId: string,
    bus: MqttBus,
    nodeDidUpdate: NodeDidUpdate,
  ) {
    const src$ = bus.streamForPoint({
      controllerId: this.controllerId,
      pointId: this.pointId,
    });
    this.sub = src$.subscribe((p: any) => {
      nodeDidUpdate(this.id, {
        presentValue: p.present_value,
        statusFlags: p.status_flags,
        properties: p.properties,
      });
    });
  }

  // BinaryInputNode is read-only; no command interface here

  // Called when node is removed from the DataGraph
  destroy(): void {
    this.sub?.unsubscribe();
    this.sub = undefined;
  }
}
```

Flow slice nodeDidUpdate implementation (single write path):

```typescript
// In flow slice, where nodes are constructed and MQTT updates are written to store
const nodeDidUpdate = (nodeId: string, patch: Record<string, unknown>) => {
  const { dataGraph } = get();

  // Get the React Flow node wrapper from DataGraph
  const reactNode = dataGraph.getNode(nodeId);
  if (!reactNode) {
    console.warn(`nodeDidUpdate: Node ${nodeId} not found in DataGraph`);
    return;
  }

  // Get the underlying DataNode instance
  const dataNode = reactNode.data as any;

  // Merge the patch into the node's discoveredProperties if present
  // This updates the data model that BACnet nodes use
  if ("discoveredProperties" in dataNode && patch) {
    dataNode.discoveredProperties = {
      ...(dataNode.discoveredProperties || {}),
      ...patch,
    };
  }

  // Optional: If you want to store runtime state separately from discoveredProperties
  // if ('runtimeState' in dataNode) {
  //   dataNode.runtimeState = { ...(dataNode.runtimeState || {}), ...patch }
  // }

  // Trigger React Flow to re-render this specific node
  // This method updates the internal node reference and marks it as changed
  dataGraph.updateNodeData(nodeId);

  // Update the Zustand store with the new nodes array
  // React Flow components will re-render based on this update
  set({ nodes: dataGraph.getNodesArray() });
};

// Usage in node construction (inside flow slice addNode action):
const bus = getMqttBus();
const dataNode = factory.createDataNodeFromBacnetConfig({
  config,
  id,
  deps: {
    bus,
    nodeDidUpdate, // Pass the callback defined above
  },
});
```

**Key points:**

- `nodeDidUpdate` is defined in flow-slice and passed to nodes during construction
- It modifies the DataNode's `discoveredProperties` in place (maintains single source of truth)
- Calls `dataGraph.updateNodeData(nodeId)` to mark the node as changed
- Updates Zustand store via `set({ nodes: ... })` to trigger React re-renders
- No direct store imports in node classes - keeps them decoupled and testable

#### 4. Real Example: AnalogInputNode changes

File: `apps/designer/src/lib/data-nodes/analog-input-node.ts`

Goal: keep the current message passing API and discoveredProperties semantics, but add MQTT-driven real-time updates using `data.point_bulk` only. The node subscribes during construction and cleans up in `destroy()`. No `subscribeMqtt` method and no `notifyGraphUpdate`.

Proposed additions inside the class (illustrative):

```typescript
import type { Subscription } from "rxjs";
import type { MqttBus } from "@/lib/mqtt/mqtt-bus";
type NodeDidUpdate = (nodeId: string, patch: Record<string, unknown>) => void;

export class AnalogInputNode implements BacnetInputOutput {
  // ...existing fields
  private mqttSub?: Subscription;

  constructor(
    config: BacnetConfig,
    bus: MqttBus,
    nodeDidUpdate: NodeDidUpdate,
    id?: string,
  ) {
    // ...existing constructor body
    const src$ = bus.streamForPoint({
      controllerId: this.controllerId,
      pointId: this.pointId,
    });
    this.mqttSub = src$.subscribe((p: any) => {
      // Update discovered properties from MQTT point payload
      // We rely on data.point_bulk only; payload fields are mapped below.
      const next: Record<string, unknown> = { ...this.discoveredProperties };
      if (p.properties) Object.assign(next, p.properties);
      if (p.present_value !== undefined) next.present_value = p.present_value;
      if (p.status_flags !== undefined) next.status_flags = p.status_flags;
      this.discoveredProperties = next as typeof this.discoveredProperties;

      // Optional: emit value downstream when it changes
      // if (p.present_value !== undefined) {
      //   const computeValue = convertToComputeValue(p.present_value)
      //   if (computeValue !== undefined) {
      //     this.send({ payload: computeValue, _msgid: uuidv4(), timestamp: Date.now() }, 'present_value')
      //   }
      // }
      // Also, write a concise runtime patch for UI
      nodeDidUpdate(this.id, {
        presentValue: p.present_value,
        statusFlags: p.status_flags,
      });
    });
  }

  // Called when node is removed
  destroy(): void {
    this.mqttSub?.unsubscribe();
    this.mqttSub = undefined;
  }
}
```

Changes required in this file:

- Add `private mqttSub?: Subscription` field.
- Subscribe inside the `constructor(config: BacnetConfig, bus: MqttBus, nodeDidUpdate: NodeDidUpdate, id?: string)` to `bus.streamForPoint({ controllerId, pointId })` (derived from `data.point_bulk`).
- Map inbound payload fields to `discoveredProperties`:
  - `present_value` → `discoveredProperties.present_value`
  - `status_flags` → `discoveredProperties.status_flags`
  - `properties` (object) → merge into `discoveredProperties`
- Also emit a minimal runtime patch via `nodeDidUpdate(nodeId, patch)` to drive UI.
- Add `destroy()` to unsubscribe.
- Do not add any `subscribeMqtt` method and do not call `notifyGraphUpdate`.
- Optional: if you want live propagation through the message system, emit on present_value change using the commented block.

Integration note: ensure the MqttBus is started before nodes are constructed so subscriptions are effective; call `node.destroy()` before removal to clean up.

Node lifecycle and destroy()

- DataGraph.removeNode should invoke `destroy()` on the underlying DataNode instance if present (similar to how it currently calls `reset()` when available) to ensure MQTT subscriptions and other resources are released.
- Flow slice actions that remove nodes must route through DataGraph.removeNode so `destroy()` is called.
- On project teardown/switch, the store should iterate all nodes and remove them via DataGraph to guarantee `destroy()` execution prior to `stopMqtt()`.

### 1. MQTT Bus Singleton (`apps/designer/src/lib/mqtt/mqtt-bus.ts`)

See updated design below for the new singleton bus implementation and APIs.

### 2. Store Integration (connection + health)

The MQTT slice is the authority for starting/stopping MQTT and stores connection + broker health. Flow slice owns graph state and node construction.

### 3. BACnet Node Binding

See updated node binding example below for subscribing at construction and reporting updates via the injected `nodeDidUpdate` callback — no manual graph notifications and no direct store imports in nodes.

### 4. UI Integration with Enhanced Status

```typescript
// In supervisors-tab.tsx
export function SupervisorsTab({ projectId }: SupervisorsTabProps) {
  const { connectionStatus, brokerHealth, lastError } = useFlowStore(
    state => ({
      connectionStatus: state.connectionStatus,
      brokerHealth: state.brokerHealth,
      lastError: state.lastError
    })
  )

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getBrokerHealthDisplay = () => {
    const icon = brokerHealth.status === 'healthy' ? '✓' :
                 brokerHealth.status === 'unhealthy' ? '✗' : '?'

    let display = `${icon} ${brokerHealth.status}`

    if (brokerHealth.uptimeSeconds) {
      const hours = Math.floor(brokerHealth.uptimeSeconds / 3600)
      display += ` (${hours}h uptime)`
    }

    return display
  }

  return (
    <div className="p-3">
      {/* MQTT 5.0 Connection Status */}
      <div className="flex items-center gap-2 mb-2">
        <div className={cn("w-2 h-2 rounded-full", getStatusColor())} />
        <span className="text-xs font-medium">MQTT 5.0: {connectionStatus}</span>
      </div>

      {/* Broker Health */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs">Broker: {getBrokerHealthDisplay()}</span>
      </div>

      {/* Last Heartbeat */}
      {brokerHealth.lastHeartbeat && (
        <div className="text-xs text-muted-foreground mb-2">
          Last heartbeat: {new Date(brokerHealth.lastHeartbeat).toLocaleTimeString()}
        </div>
      )}

      {/* Error Display */}
      {lastError && (
        <div className="text-xs text-red-600 mb-2">
          Error: {lastError}
        </div>
      )}

      {/* MQTT Version */}
      {brokerHealth.version && (
        <div className="text-xs text-muted-foreground mb-2">
          Version: {brokerHealth.version}
        </div>
      )}

      {/* Rest of existing UI */}
    </div>
  )
}
```

## Implementation Plan

### Overview

The implementation follows a phased approach, focusing on **read behavior first** with a single example node per type to validate the inheritance pattern before bulk migration. Write commands are deferred to future phases.

---

### **Phase 1: Foundation (MQTT Infrastructure)**

**Goal:** Establish MQTT connectivity and core infrastructure without touching existing nodes

**Deliverables:**

1. Install dependencies

   ```bash
   pnpm add mqtt rxjs
   pnpm add -D @types/mqtt
   ```

2. Create `MqttBus` singleton (`apps/designer/src/lib/mqtt/mqtt-bus.ts`)

   - Connection management with exponential backoff (1s, 2s, 4s, 8s, 16s, 30s max)
   - RxJS streams: `connectionStatus$`, `heartbeatStream$`, `pointBulkStream$`
   - `streamForPoint(ids)` with error handling and validation
   - `request<T>(command, payload, timeout)` for MQTT 5.0 request/response
   - SSR guards and idempotent `start()`/`stop()`

3. Create `MQTTSlice` in Zustand store

   - State: `connectionStatus`, `brokerHealth`, `lastError`
   - Actions: `startMqtt(config)`, `stopMqtt()`, `sendCommand(command, payload)`
   - Subscribe to bus streams (connection status, heartbeat)
   - Heartbeat watchdog (35s threshold)

4. Update `DataGraph.removeNode()` to call `destroy()` before `reset()`

   ```typescript
   // CRITICAL: Call destroy() FIRST to cleanup MQTT subscriptions
   if ("destroy" in dataNode && typeof dataNode.destroy === "function") {
     dataNode.destroy();
   }
   // Then call reset() to cleanup timers/intervals
   if ("reset" in dataNode && typeof dataNode.reset === "function") {
     dataNode.reset();
   }
   ```

5. Add `clearAllNodes()` action to flow-slice

   - Iterates all nodes and calls `dataGraph.removeNode(id)` (which triggers `destroy()`)

6. Add startup sequence logic to project workspace

   - Stop existing MQTT → clear all nodes → start MQTT → wait for 'connected' → load workflow

7. Update SupervisorsTab UI with connection indicators
   - Connection status (green/yellow/red dot)
   - Broker health (healthy/unhealthy icon)
   - Last heartbeat timestamp
   - Uptime display

**Testing:**

- MQTT connection/reconnection with exponential backoff
- Heartbeat monitoring (healthy → unhealthy after 35s silence)
- Connection status UI updates
- SSR guard (no connection during Next.js build)

**Success Criteria:** Green connection indicator in SupervisorsTab, heartbeat visible, no memory leaks on reconnect

**Risk:** Low - no node changes

---

### **Phase 2: get_config Command Infrastructure**

**Goal:** Implement `get_config` request/response to retrieve device configuration

**Deliverables:**

1. Verify `get_config` command in MqttBus.request()

   - Uses MQTT 5.0 `correlationData` and `responseTopic` properties
   - Filters response by correlation ID
   - Handles timeout (30s default)
   - Returns Observable<T>

2. Add `getConfig()` action to MQTT slice

   ```typescript
   getConfig: async () => {
     const bus = getMqttBus();
     return bus.request(CommandNameEnum.GET_CONFIG, {}, 30000).toPromise();
   };
   ```

3. Create UI trigger in SupervisorsTab

   - "Get Config" button
   - Loading state during request
   - Display response in expandable JSON viewer or structured table

4. Handle error cases
   - Timeout → show error toast
   - Connection lost → disable button
   - Invalid response → log and show error

**Testing:**

- Click "Get Config" button
- Verify MQTT message published with correlation ID
- Receive response on correct response topic
- Correlation ID matches request
- Timeout handling (mock delayed/no response)
- Display response data in UI

**Success Criteria:** Button triggers get_config, response displays in UI within 30s, timeout handled gracefully

**Risk:** Low - testing infrastructure only, no node changes

---

### **Phase 3: Base BACnet Node + Single Input Node**

**Goal:** Create reusable `BaseBacnetNode` abstract class and migrate ONE input node to prove the pattern

**Target Node:** `AnalogInputNode` (read-only, safest to start)

**Deliverables:**

1. **Create `BaseBacnetNode` abstract class** (`apps/designer/src/lib/data-nodes/base-bacnet-node.ts`)

   ```typescript
   export abstract class BaseBacnetNode implements BacnetInputOutput {
     // Common BACnet fields
     readonly pointId: string;
     readonly objectId: number;
     readonly supervisorId: string;
     readonly controllerId: string;
     discoveredProperties: BacnetProperties;
     readonly name: string;
     readonly position?: { x: number; y: number };
     readonly id: string;
     readonly category = NodeCategory.BACNET;
     readonly label: string;

     // Message system
     private sendCallback?: SendCallback<BacnetOutputHandle>;

     // MQTT subscription
     private mqttSub?: Subscription;

     // Abstract properties (subclasses must define)
     abstract readonly type: NodeType;
     abstract readonly objectType: BacnetObjectType;
     abstract readonly direction: NodeDirection;

     constructor(
       config: BacnetConfig,
       bus: MqttBus,
       nodeDidUpdate: NodeDidUpdate,
       id?: string,
     ) {
       // Initialize all fields from config
       // Subscribe to bus.streamForPoint({ controllerId, pointId })
       // On MQTT update: handleMqttUpdate() + nodeDidUpdate()
     }

     // Shared implementations
     getInputHandles(): readonly BacnetInputHandle[] {
       /* shared logic */
     }
     getOutputHandles(): readonly BacnetOutputHandle[] {
       /* shared logic */
     }
     toSerializable(): Record<string, unknown> {
       /* shared logic */
     }
     setSendCallback(callback: SendCallback<BacnetOutputHandle>): void {
       /* shared */
     }

     destroy(): void {
       this.mqttSub?.unsubscribe();
       this.mqttSub = undefined;
     }

     // Template method - subclasses can override
     protected handleMqttUpdate(payload: any): void {
       // Default: merge payload into discoveredProperties
       if (payload.properties)
         Object.assign(this.discoveredProperties, payload.properties);
       if (payload.present_value !== undefined)
         this.discoveredProperties.present_value = payload.present_value;
       if (payload.status_flags !== undefined)
         this.discoveredProperties.status_flags = payload.status_flags;
     }

     // Subclasses implement message routing
     abstract receive(
       message: Message,
       handle: BacnetInputHandle,
       fromNodeId: string,
     ): Promise<void>;
     abstract canConnectWith(other: DataNode): boolean;
   }
   ```

2. **Refactor `AnalogInputNode` to extend `BaseBacnetNode`**

   ```typescript
   export class AnalogInputNode extends BaseBacnetNode {
     readonly type = NodeType.ANALOG_INPUT;
     readonly objectType = "analog-input" as const;
     readonly direction = NodeDirection.OUTPUT;

     canConnectWith(target: DataNode): boolean {
       return target.direction !== NodeDirection.OUTPUT;
     }

     async receive(
       message: Message,
       handle: BacnetInputHandle,
       fromNodeId: string,
     ): Promise<void> {
       // Existing message routing logic (preserve as-is)
     }
   }
   ```

3. **Update factory to accept `deps`**

   ```typescript
   createDataNodeFromBacnetConfig({
     config,
     id,
     deps, // NEW: { bus: MqttBus, nodeDidUpdate: NodeDidUpdate }
   }: {
     config: BacnetConfig
     id?: string
     deps?: { bus: MqttBus; nodeDidUpdate: NodeDidUpdate }
   }): BacnetInputOutput {
     const { objectType } = config

     // Only AnalogInputNode updated in Phase 3
     if (objectType === 'analog-input' && deps) {
       return new AnalogInputNode(config, deps.bus, deps.nodeDidUpdate, id)
     }

     // Other nodes use old constructor (backward compatible)
     switch (objectType) {
       case 'analog-input':
         return new AnalogInputNode(config, id) // Fallback if no deps
       // ... rest unchanged
     }
   }
   ```

4. **Implement `nodeDidUpdate` in flow-slice**

   ```typescript
   const nodeDidUpdate = (nodeId: string, patch: Record<string, unknown>) => {
     const { dataGraph } = get();
     const reactNode = dataGraph.getNode(nodeId);
     if (!reactNode) {
       console.warn(`nodeDidUpdate: Node ${nodeId} not found`);
       return;
     }

     const dataNode = reactNode.data as any;
     if ("discoveredProperties" in dataNode && patch) {
       dataNode.discoveredProperties = {
         ...(dataNode.discoveredProperties || {}),
         ...patch,
       };
     }

     dataGraph.updateNodeData(nodeId);
     set({ nodes: dataGraph.getNodesArray() });
   };
   ```

5. **Update flow-slice node creation to pass deps**

   ```typescript
   const bus = getMqttBus();
   const dataNode = factory.createDataNodeFromBacnetConfig({
     config,
     id,
     deps: { bus, nodeDidUpdate },
   });
   ```

6. **Update deserializer to inject deps**
   ```typescript
   export function createNodeFactoryWithDeps(deps: {
     bus: MqttBus;
     nodeDidUpdate: NodeDidUpdate;
   }) {
     return function nodeFactory(
       nodeType: string,
       data: Record<string, unknown>,
     ) {
       if (nodeType === "bacnet.analog-input") {
         return factory.createDataNodeFromBacnetConfig({
           config: data.metadata as BacnetConfig,
           id: data.id as string,
           deps,
         });
       }
       // ... existing logic for other nodes
     };
   }
   ```

**Testing:**

- Drop `AnalogInputNode` on canvas
- Verify MQTT subscription created (check logs)
- Publish `point_bulk` message via MQTT client
- See live `present_value` update in node UI
- Delete node → verify `destroy()` called and subscription cleaned up
- Reload workflow → verify node reconnects

**Success Criteria:**

- ONE `AnalogInputNode` shows live MQTT data updates
- No memory leaks on node delete
- Deserializer reconstructs node with MQTT active

**Risk:** Medium - first node migration, backward compatibility maintained

---

### **Phase 4: Single Value Node (Bidirectional, Read-Only)**

**Goal:** Add MQTT to ONE value node to test bidirectional pattern (read behavior only)

**Target Node:** `AnalogValueNode` (bidirectional, but only read behavior for now)

**Deliverables:**

1. Refactor `AnalogValueNode` to extend `BaseBacnetNode`

   - Same pattern as Phase 3
   - Focus on MQTT read updates only (no write commands)

2. Update factory to handle `analog-value` with deps
3. Update deserializer for `bacnet.analog-value`

**Testing:**

- Drop `AnalogValueNode` on canvas
- Verify real-time updates from `point_bulk`
- Verify UI refresh on property changes
- Delete node → verify cleanup

**Success Criteria:** `AnalogValueNode` displays live MQTT data

**Risk:** Low - same pattern as Phase 3

---

### **Phase 5: Single Output Node (Read Behavior)**

**Goal:** Add MQTT to ONE output node (showing read state, no write commands)

**Target Node:** `AnalogOutputNode` (write-only node, but showing current read state)

**Deliverables:**

1. Refactor `AnalogOutputNode` to extend `BaseBacnetNode`
2. Show current output state from MQTT (read-only)
3. No write command implementation yet (deferred to future phase)

**Testing:**

- Drop `AnalogOutputNode` on canvas
- Display current device state from `point_bulk`
- Verify UI updates

**Success Criteria:** `AnalogOutputNode` shows current device state via MQTT

**Risk:** Low - read-only, consistent pattern

---

### **Phase 6: Remaining Nodes (Bulk Migration)**

**Goal:** Extend remaining 6 BACnet nodes using proven pattern

**Target Nodes:**

- BinaryInputNode
- BinaryValueNode
- BinaryOutputNode
- MultistateInputNode
- MultistateValueNode
- MultistateOutputNode

**Deliverables:**

1. Refactor each to extend `BaseBacnetNode`
2. All read-only (no write commands)
3. Update factory for all 9 BACnet node types
4. Update deserializer for all types

**Testing:**

- Test each node type with live MQTT data
- Verify cleanup on delete for all nodes
- Load workflows with multiple node types

**Success Criteria:** All 9 BACnet nodes display live MQTT data, no memory leaks

**Risk:** Low - proven pattern from Phases 3-5

---

### **Phase 7: Write Commands (Future - Out of Scope)**

**Goal:** Add write operations using `set_value_to_point` command

**Deferred:** Focus on read/display first. Write commands require:

- Command integration in BaseBacnetNode
- Write acknowledgment handling
- Priority and override mode support
- Error handling for write failures

---

## Key Design Decisions

### Focus on Read Behavior

- All phases prioritize **displaying live data** from MQTT `point_bulk` topic
- No write operations until read behavior is proven and stable
- `get_config` command tested early to validate MQTT 5.0 request/response pattern

### Inheritance Pattern

- `BaseBacnetNode` eliminates duplication across 9 BACnet node types
- Template method pattern for `handleMqttUpdate()` allows customization
- Abstract properties force subclasses to define `type`, `objectType`, `direction`
- Backward compatibility maintained in factory (old constructors still work)

### Incremental Rollout

- **One example node per type** (Input, Value, Output) validates pattern before bulk migration
- Phases 3-5 are intentionally limited to one node each
- Phase 6 uses proven pattern for remaining 6 nodes

### Testing Strategy

- Each phase has explicit success criteria
- Manual testing with real MQTT broker and `point_bulk` messages
- Memory leak detection (destroy() cleanup verification)
- Workflow serialization/deserialization validation

## Testing Scenarios

1. **MQTT 5.0 Features**

   - Correlation data properly set and matched
   - Response topics correctly used
   - QoS levels respected
   - Retain flags honored

2. **All Command Types**

   - get_config request/response
   - set_value_to_point with proper parameters
   - start_monitoring/stop_monitoring
   - reboot command
   - Alert acknowledge/resolve

3. **Real-time Updates**

   - Individual point data updates via `streamForPoint`
   - Bulk point data merged transparently
   - Heartbeat monitoring and timeout detection

4. **Error Scenarios**
   - Request timeout handling
   - Connection loss and reconnection
   - Invalid command responses
   - Malformed MQTT messages

## Notes on Removed/Deprecated Patterns

- Per-node `subscribeMqtt(mqttService)` is deprecated. Nodes subscribe at creation via injected `MqttBus` domain streams.
- `notifyGraphUpdate()` is removed. Runtime updates are written directly to the store from the RxJS pipeline; React derives from state.

---

## Phase 1 Test Plan

### Testing Principles

1. **DO NOT mock the system under test** - Test actual implementations
2. **Mock external dependencies only** - Mock MQTT.js library, browser APIs, external services
3. **Unit tests** - Can mock other Designer modules (e.g., mock DataGraph when testing MQTT slice)
4. **Integration/E2E tests** - Mock only external libraries (MQTT client, WebSocket)
5. **Focus on behavior** - Test user-visible outcomes, not implementation details

### What We Mock vs What We Test

**Mocked (External Dependencies):**

- ✅ External libraries: `mqtt`, `uuid`
- ✅ Browser APIs: `window.location`
- ✅ Designer modules (in unit tests only): `getMqttBus()`, API hooks

**NOT Mocked (System Under Test):**

- ❌ MQTT slice logic
- ❌ MqttBus implementation
- ❌ SupervisorsTab component
- ❌ RxJS observables (test actual behavior)
- ❌ Zustand store logic

---

### 1. Unit Tests - MQTT Slice (`mqtt-slice.spec.ts`)

**System Under Test:** `createMQTTSlice`
**Mocks:** `getMqttBus()` (Designer module), RxJS timer functions

#### Test Suites

**Initial State**

- Should initialize with `connectionStatus: 'disconnected'`
- Should initialize with `brokerHealth.status: 'unknown'`
- Should have no `lastError` initially

**startMqtt()**

- Should call `getMqttBus().start()` with correct config
- Should update `connectionStatus` when bus emits status changes
- Should set broker health to 'healthy' when heartbeat received
- Should store heartbeat payload in `lastHeartbeat`
- Should update `lastHeartbeatTimestamp` to current time
- Should set broker status to 'unhealthy' on heartbeat stream error
- Should set `lastError` when heartbeat stream errors

**Heartbeat Watchdog (60s threshold)**

- Should mark broker 'unhealthy' when no heartbeat for >60s
- Should mark broker 'healthy' when heartbeat received within 60s
- Should not change status if already 'unhealthy' and still silent
- Should not change status if already 'healthy' and still receiving
- Should handle missing `lastHeartbeatTimestamp` gracefully

**stopMqtt()**

- Should call `getMqttBus().stop()`
- Should complete the `mqttStop$` Subject
- Should reset `connectionStatus` to 'disconnected'
- Should reset `brokerHealth.status` to 'unknown'
- Should clear `lastError`
- Should unsubscribe from all RxJS streams

**sendCommand()**

- Should call `bus.request()` with command and payload
- Should return Promise from `toPromise()`
- Should handle command errors

---

### 2. Unit Tests - MQTT Bus (`mqtt-bus.spec.ts`)

**System Under Test:** `MqttBusCore`
**Mocks:** `mqtt` library (external), `window.location` (browser API)

#### Test Suites

**Connection**

- Should connect to MQTT broker with correct URL
- Should use `ws://` for http:// pages
- Should use `wss://` for https:// pages
- Should emit 'connecting' status during connection
- Should emit 'connected' status on successful connection
- Should emit 'error' status on connection failure
- Should use MQTT 5.0 protocol version
- Should set clean session to true

**Subscriptions**

- Should subscribe to heartbeat topic on connect
- Should subscribe to point_bulk topic on connect
- Should subscribe to all command response topics
- Should use correct QoS levels (0, 1, or 2)
- Should pass correct topic strings with org_id/site_id/iot_device_id

**Heartbeat Stream**

- Should emit heartbeat payloads to `heartbeatStream$`
- Should parse JSON heartbeat messages
- Should handle malformed heartbeat JSON gracefully
- Should route heartbeat messages to correct stream

**Point Bulk Stream**

- Should emit point_bulk payloads to `pointBulkStream$`
- Should parse JSON point_bulk messages
- Should route point_bulk messages to correct stream

**Cleanup**

- Should disconnect client on `stop()`
- Should complete all observables on `stop()`
- Should set connection status to 'disconnected'
- Should handle stop() when not connected

**MqttBusManager Singleton**

- Should return same instance for `getMqttBus()`
- Should create new core when `start()` called with new config
- Should reuse existing connection when config unchanged

---

### 3. Component Tests - SupervisorsTab (`supervisors-tab.spec.tsx`)

**System Under Test:** `SupervisorsTab` component
**Mocks:** API hooks (`useDeploymentConfig`, `useUpdateDeploymentConfig`), Zustand selectors

#### Test Suites

**Rendering States**

- Should show loading state while fetching config
- Should show "No Supervisor Configured" when no config
- Should show "Configure Supervisor" button when no config
- Should show deployment config when configured
- Should show edit button when config exists

**Configuration Form**

- Should validate organization*id starts with "org*"
- Should enable save button when all fields valid
- Should disable save button when fields empty
- Should disable save button when org_id invalid
- Should call update mutation on save
- Should reset form on cancel
- Should show validation errors

**MQTT Status Display**

- Should show connection status badge (connected/connecting/disconnected/error)
- Should show correct color for each status (green/yellow/gray/red)
- Should show broker health badge (healthy/unhealthy/unknown)
- Should display uptime in human-readable format (666s = "11m 6s")
- Should display monitoring status badge
- Should display last heartbeat timestamp
- Should show "Waiting for heartbeat..." when connected but no data
- Should show pulsing icon when waiting

**Timestamp Conversion**

- Should convert Unix timestamp seconds to milliseconds (multiply by 1000)
- Should display correct local time (not 1970)
- Should format timestamp using toLocaleTimeString()

**Error States**

- Should show error message when lastError exists
- Should show AlertCircle icon for errors
- Should show "Waiting for heartbeat..." with helper text when no heartbeat
- Should indicate config mismatch possibility in helper text

---

### 4. Integration Test - Full MQTT Lifecycle (`mqtt-integration.spec.tsx`)

**System Under Test:** MQTT slice + MqttBus + SupervisorsTab together
**Mocks:** Only `mqtt` library (external)

#### Test Suite

**Full Connection Lifecycle**

- Configure deployment settings
- Start MQTT connection
- Verify connection status changes to 'connected'
- Simulate BMS heartbeat message on correct topic
- Verify UI shows heartbeat data
- Verify broker health shows 'healthy'
- Verify uptime displays correctly
- Stop MQTT connection
- Verify cleanup and status reset to 'disconnected'
- Verify broker health resets to 'unknown'

**Error Recovery**

- Start connection
- Simulate connection error
- Verify status shows 'error'
- Verify reconnection attempt with exponential backoff
- Simulate successful reconnect
- Verify status returns to 'connected'

**Heartbeat Timeout**

- Start connection and receive initial heartbeat
- Verify broker health is 'healthy'
- Advance time by 65 seconds (past 60s threshold)
- Verify broker health changes to 'unhealthy'
- Send new heartbeat
- Verify broker health returns to 'healthy'

---

### Test Utilities & Helpers

**Mock MQTT Client**

```typescript
const createMockMqttClient = () => ({
  on: jest.fn(),
  subscribe: jest.fn(),
  publish: jest.fn(),
  end: jest.fn(),
  connected: false,
});
```

**Mock Heartbeat Payload**

```typescript
const createMockHeartbeat = (): HeartbeatPayload => ({
  cpu_usage_percent: 10.5,
  memory_usage_percent: 75.2,
  disk_usage_percent: 45.3,
  temperature_celsius: null,
  uptime_seconds: 666,
  load_average: 1.5,
  monitoring_status: "active",
  mqtt_connection_status: "connected",
  bacnet_connection_status: null,
  bacnet_devices_connected: null,
  bacnet_points_monitored: null,
  timestamp: Date.now() / 1000, // Unix timestamp in seconds
  organization_id: "org_test",
  site_id: "site-123",
  iot_device_id: "device-456",
});
```

**Timer Helpers**

```typescript
// For watchdog tests
jest.useFakeTimers();
jest.advanceTimersByTime(65_000);
jest.useRealTimers();

// Wait for RxJS subscriptions
await waitFor(() => expect(condition).toBe(true));

// Mock Date.now() for timestamp tests
jest.spyOn(Date, "now").mockReturnValue(1759364179000);
```

---

### Success Criteria

**Phase 1 Tests Complete When:**

- ✅ All MQTT slice unit tests pass
- ✅ All MQTT bus unit tests pass
- ✅ All SupervisorsTab component tests pass
- ✅ Integration test validates full lifecycle
- ✅ No memory leaks detected (subscriptions cleaned up)
- ✅ Timestamp conversion works correctly (seconds → milliseconds)
- ✅ Error states properly handled and displayed
- ✅ Tests run in CI without flakiness

**Test Coverage Goals:**

- MQTT slice: >90%
- MQTT bus: >85%
- SupervisorsTab: >80%
- Overall Phase 1 code: >85%

---

### Implementation Order

1. **mqtt-slice.spec.ts** - Foundation tests for state management
2. **mqtt-bus.spec.ts** - Core MQTT infrastructure tests
3. **supervisors-tab.spec.tsx** - UI component tests
4. **mqtt-integration.spec.tsx** - End-to-end validation

Each test file should be implemented completely before moving to the next to ensure foundational behavior is validated before testing integration.
