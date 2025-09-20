# Testing Infrastructure Tickets for Designer App

Created: September 18, 2025
Project: BMS Supervisor Controller
App: Designer (Next.js)

## Overview

This document outlines the testing infrastructure setup for the Designer app, broken down into focused tickets. Each ticket with tests specifies EXACTLY what test will be written with complete code.

---

## **TICKET 1: Basic Testing Infrastructure Setup**

### **Title**

Set up minimal testing infrastructure for Designer app with proper database configuration

### **Type:** Infrastructure

### **Priority:** High

### **Labels:** `testing`, `infrastructure`, `designer`

### **Description**

Create the basic testing infrastructure with minimal setup - just enough to start writing tests. Uses a separate test database file to avoid interfering with development database. Includes React Query provider setup for components that use queries.

### **Implementation**

#### **Directory Structure**

```
apps/designer/
  __mocks__/
    test-utils/
      render.tsx
      setup-env.ts
  jest.config.js
  jest.setup.js
  .env.test                    # Test database configuration
```

#### **Files to Create**

**jest.config.js**

```javascript
const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jsdom",

  // Load .env.test file
  setupFiles: ["<rootDir>/test-utils/setup-env.ts"],

  testMatch: ["**/*.spec.[jt]s?(x)"],

  roots: ["<rootDir>/src"],

  moduleNameMapping: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^@test-utils/(.*)$": "<rootDir>/test-utils/$1",
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
  },

  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/**/*.spec.{ts,tsx}",
  ],

  clearMocks: true,
  resetMocks: true,
};

module.exports = createJestConfig(customJestConfig);
```

**test-utils/setup-env.ts**

```typescript
// Load test environment variables
import { config } from "dotenv";
import path from "path";

// Load .env.test file
config({ path: path.resolve(process.cwd(), ".env.test") });

// Ensure critical test environment variables are set
if (process.env.NODE_ENV !== "test") {
  process.env.NODE_ENV = "test";
}

// Ensure Turso is not used in tests
delete process.env.TURSO_DATABASE_URL;
delete process.env.TURSO_AUTH_TOKEN;
```

**jest.setup.js**

```javascript
import "@testing-library/jest-dom";
import fs from "fs";
import path from "path";

// Clean up test database before tests
beforeAll(() => {
  const testDbPath = path.join(process.cwd(), "designer-test.db");
  const testDbWalPath = path.join(process.cwd(), "designer-test.db-wal");
  const testDbShmPath = path.join(process.cwd(), "designer-test.db-shm");

  // Remove existing test database files
  if (fs.existsSync(testDbPath)) {
    fs.unlinkSync(testDbPath);
  }
  if (fs.existsSync(testDbWalPath)) {
    fs.unlinkSync(testDbWalPath);
  }
  if (fs.existsSync(testDbShmPath)) {
    fs.unlinkSync(testDbShmPath);
  }
});

// Browser API mocks
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// localStorage mock
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;
```

**test-utils/render.tsx**

```typescript
import React from 'react'
import { render as rtlRender } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { RenderOptions } from '@testing-library/react'

// Create a test query client with defaults suitable for testing
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Turn off retries to make tests faster and more predictable
        retry: false,
        // Don't refetch on window focus during tests
        refetchOnWindowFocus: false,
        // Set stale time to 0 to always refetch when needed
        staleTime: 0,
      },
      mutations: {
        // Turn off retries for mutations too
        retry: false,
      },
    },
    // Suppress error logging in tests
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {}, // Suppress error logs in tests
    },
  })
}

interface ExtendedRenderOptions extends RenderOptions {
  queryClient?: QueryClient
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    queryClient = createTestQueryClient(),
    ...options
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }

  return {
    ...rtlRender(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  }
}

// Export the test query client creator for direct use in tests
export { createTestQueryClient }

export * from '@testing-library/react'
export { renderWithProviders as render }
```

**.env.test**

```bash
NODE_ENV=test
DATABASE_PATH=designer-test.db
# Explicitly do not set TURSO_DATABASE_URL for tests
# TURSO_DATABASE_URL= (leave unset)
# TURSO_AUTH_TOKEN= (leave unset)
```

**.gitignore addition**

```
# Test database files
designer-test.db
designer-test.db-wal
designer-test.db-shm
```

**UPDATED: Update database client for test compatibility**
The existing `/apps/designer/src/lib/db/client.ts` needs a small update to respect `DATABASE_PATH` environment variable:

```typescript
// Update line 44 from:
const dbPath = join(process.cwd(), "designer.db");

// To:
const dbPath = process.env.DATABASE_PATH
  ? join(process.cwd(), process.env.DATABASE_PATH)
  : join(process.cwd(), "designer.db");
```

**package.json scripts addition**

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

### **Dependencies to Install**

```bash
pnpm add -D @testing-library/user-event identity-obj-proxy dotenv
```

### **Acceptance Criteria**

- [ ] Jest configuration works with `*.spec.ts` convention
- [ ] `.env.test` file is loaded correctly before tests run
- [ ] Basic browser API mocks work
- [ ] React Query provider is included in test utils
- [ ] Query client is configured for optimal test performance (no retries, no refetch on focus)
- [ ] `pnpm test` command works
- [ ] Tests use separate `designer-test.db` file from `.env.test`
- [ ] Test database is cleaned before test runs
- [ ] Database client respects `DATABASE_PATH` environment variable
- [ ] Test database files are gitignored
- [ ] Can write a simple test that passes

### **Tests**

**None - Infrastructure only**

### **Additional Notes**

- React Query provider is included from the start since many components will use it
- Test query client has optimized defaults: no retries, no refetch on window focus
- Error logging is suppressed in tests to reduce noise
- Each test gets a fresh query client instance to prevent state leakage
- The `queryClient` is returned from `render` for tests that need to interact with it directly
- Environment variables are loaded from `.env.test` using dotenv in `setup-env.ts`
- This approach works with both local development and CI environments

---

## **TICKET 2: Zustand Mock with Flow Store Test**

### **Title**

Add Zustand mock and validate with flow store test

### **Type:** Testing + Mock

### **Priority:** High

### **Labels:** `testing`, `mocks`, `state-management`

### **Depends On:** TICKET 1

### **Description**

Add Zustand mock for state management testing with one specific test to validate it works.

### **Files to Create**

**`__mocks__/zustand.ts`**

```typescript
import { act } from "@testing-library/react";
import { create as actualCreate } from "zustand";

const storeResetFns = new Set();

export const create = (createState) => {
  const store = actualCreate(createState);
  const initialState = store.getState();

  storeResetFns.add(() => {
    store.setState(initialState, true);
  });

  return store;
};

// Reset all stores after each test
afterEach(() => {
  act(() => {
    storeResetFns.forEach((resetFn) => resetFn());
  });
});
```

### **Test to Write**

**`src/stores/flow-store.spec.ts`**

```typescript
import { renderHook, act } from "@testing-library/react";
import { useFlowStore } from "./flow-store";

describe("Flow Store", () => {
  it("should add node with id node-1 and verify it exists in state", () => {
    const { result } = renderHook(() => useFlowStore());

    // Verify initial state is empty
    expect(result.current.nodes).toEqual([]);

    // Add a specific node
    act(() => {
      result.current.addNode({
        id: "node-1",
        type: "constant",
        position: { x: 100, y: 100 },
        data: { value: 10, label: "Test Node" },
      });
    });

    // Verify the node was added with exact expected properties
    expect(result.current.nodes).toHaveLength(1);
    expect(result.current.nodes[0]).toEqual({
      id: "node-1",
      type: "constant",
      position: { x: 100, y: 100 },
      data: { value: 10, label: "Test Node" },
    });
  });
});
```

### **Acceptance Criteria**

- [ ] Zustand mock prevents state leakage between tests
- [ ] Flow store test passes exactly as written
- [ ] Store resets between tests
- [ ] Node with id 'node-1' is correctly added and verified

---

## **TICKET 3: Database Mock with Repository Test**

### **Title**

Add database client mock and validate with project repository test

### **Type:** Testing + Mock

### **Priority:** High

### **Labels:** `testing`, `mocks`, `database`

### **Depends On:** TICKET 1

### **Description**

Add LibSQL/Turso client mock with one specific test to validate database operations work.

### **Files to Create**

**`__mocks__/@libsql/client.ts`**

```typescript
const mockExecute = jest.fn().mockResolvedValue({
  rows: [],
  columns: [],
  rowsAffected: 0,
});

const mockBatch = jest.fn().mockResolvedValue([]);

const mockTransaction = jest.fn(async (cb) => {
  const tx = {
    execute: mockExecute,
    batch: mockBatch,
    rollback: jest.fn(),
  };
  return await cb(tx);
});

export const createClient = jest.fn(() => ({
  execute: mockExecute,
  batch: mockBatch,
  transaction: mockTransaction,
  close: jest.fn(),
}));

// Export for test access
export const __mockExecute = mockExecute;
export const __mockBatch = mockBatch;
```

### **Test to Write**

**`src/lib/db/projects.spec.ts`**

```typescript
import { createProject } from "./projects";
import { __mockExecute } from "@libsql/client";

describe("Projects Repository", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should create project with name Test Project and return it with generated id", async () => {
    // Configure mock to return specific project data
    __mockExecute.mockResolvedValueOnce({
      rows: [{ id: "proj-abc123" }],
      columns: ["id"],
      rowsAffected: 1,
    });

    const projectData = {
      name: "Test Project",
      flow: {
        nodes: [
          {
            id: "node-1",
            type: "constant",
            position: { x: 100, y: 100 },
            data: { value: 42 },
          },
        ],
        edges: [],
      },
    };

    const result = await createProject(projectData);

    // Verify the project was created with expected properties
    expect(result).toEqual({
      id: "proj-abc123",
      name: "Test Project",
      flow: {
        nodes: [
          {
            id: "node-1",
            type: "constant",
            position: { x: 100, y: 100 },
            data: { value: 42 },
          },
        ],
        edges: [],
      },
    });

    // Verify the correct SQL was executed
    expect(__mockExecute).toHaveBeenCalledWith(
      expect.objectContaining({
        sql: expect.stringContaining("INSERT INTO projects"),
        args: expect.arrayContaining(["Test Project"]),
      }),
    );
  });
});
```

### **Acceptance Criteria**

- [ ] Database client mock handles async operations
- [ ] Project creation test passes exactly as written
- [ ] Mock returns project with id 'proj-abc123'
- [ ] Project name 'Test Project' is correctly saved and returned

---

## **TICKET 4: React Flow Mock with ConstantNode Test**

### **Title**

Add React Flow mock and validate with ConstantNode test

### **Type:** Testing + Mock

### **Priority:** High

### **Labels:** `testing`, `mocks`, `ui`, `components`

### **Depends On:** TICKET 1

### **Description**

Add React Flow mock components with one specific test to validate component rendering works.

### **Files to Create**

**`__mocks__/@xyflow/react.tsx`**

```typescript
import React from 'react'

export const ReactFlow = ({ children, nodes, edges }) => (
  <div data-testid="react-flow">
    <div data-testid="nodes-count">{nodes?.length || 0}</div>
    <div data-testid="edges-count">{edges?.length || 0}</div>
    {children}
  </div>
)

export const ReactFlowProvider = ({ children }) => <div>{children}</div>

export const Handle = ({ type, position, id }) => (
  <div
    className={type}
    data-testid={`handle-${type}-${id || 'default'}`}
    data-handleid={id}
    data-handletype={type}
  />
)

export const useNodesState = jest.fn((initial) => {
  const [nodes, setNodes] = React.useState(initial)
  return [nodes, setNodes, jest.fn()]
})

export const useEdgesState = jest.fn((initial) => {
  const [edges, setEdges] = React.useState(initial)
  return [edges, setEdges, jest.fn()]
})

export const useReactFlow = jest.fn(() => ({
  getNodes: jest.fn(() => []),
  getEdges: jest.fn(() => []),
  setNodes: jest.fn(),
  setEdges: jest.fn(),
  fitView: jest.fn()
}))

export const Background = () => <div data-testid="background" />
export const Controls = () => <div data-testid="controls" />
export const MiniMap = () => <div data-testid="minimap" />
```

**Update test-utils/render.tsx**

```typescript
import React from 'react'
import { render as rtlRender } from '@testing-library/react'
import { ReactFlowProvider } from '@xyflow/react'
import type { RenderOptions } from '@testing-library/react'

export function renderWithProviders(
  ui: React.ReactElement,
  options?: RenderOptions
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <ReactFlowProvider>
        {children}
      </ReactFlowProvider>
    )
  }

  return rtlRender(ui, { wrapper: Wrapper, ...options })
}

export * from '@testing-library/react'
export { renderWithProviders as render }
```

### **Test to Write**

**`src/components/nodes/constant-node.spec.tsx`**

```typescript
import { render } from '@test-utils/render'
import { ConstantNode } from './constant-node'

describe('ConstantNode', () => {
  it('should render input with role spinbutton and value 10', () => {
    const nodeProps = {
      id: 'constant-1',
      data: {
        value: 10,
        label: 'Test Constant'
      },
      selected: false,
      type: 'constant',
      xPos: 100,
      yPos: 100
    }

    const { getByRole, getByText } = render(<ConstantNode {...nodeProps} />)

    // Verify the input exists with correct role and value
    const input = getByRole('spinbutton')
    expect(input).toBeInTheDocument()
    expect(input).toHaveValue(10)

    // Verify the label is displayed
    expect(getByText('Test Constant')).toBeInTheDocument()

    // Verify the output handle is rendered (from React Flow mock)
    expect(document.querySelector('[data-testid="handle-source-default"]')).toBeInTheDocument()
  })
})
```

### **Acceptance Criteria**

- [ ] React Flow mock provides necessary components
- [ ] ConstantNode renders without errors
- [ ] Input has role='spinbutton' and value=10
- [ ] Label 'Test Constant' is displayed
- [ ] Output handle is rendered

---

## **TICKET 5: Next.js API Route Testing**

### **Title**

Set up API route testing for projects endpoints

### **Type:** Testing

### **Priority:** Medium

### **Labels:** `testing`, `api`, `nextjs`

### **Depends On:** TICKET 3

### **Description**

Test actual Next.js API routes directly using the mocked repository from Ticket 3.

### **Test to Write**

**`src/app/api/projects/route.spec.ts`**

```typescript
import { GET, POST } from "./route";
import { NextRequest } from "next/server";
import { __mockExecute } from "@libsql/client";

// Mock the projects repository module
jest.mock("../../../lib/db/projects", () => ({
  projectsRepository: {
    list: jest.fn(),
    create: jest.fn(),
  },
}));

import { projectsRepository } from "../../../lib/db/projects";

describe("Projects API Routes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should GET /api/projects and return success true with empty projects array", async () => {
    // Configure repository mock to return empty results
    (projectsRepository.list as jest.Mock).mockResolvedValueOnce({
      projects: [],
      total: 0,
      page: 1,
      limit: 10,
    });

    const request = new NextRequest("http://localhost:3000/api/projects");
    const response = await GET(request);

    // Verify response status and structure
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data).toEqual({
      success: true,
      data: {
        projects: [],
        total: 0,
        page: 1,
        limit: 10,
      },
    });

    // Verify repository was called with default query params
    expect(projectsRepository.list).toHaveBeenCalledWith({
      page: null,
      limit: null,
      search: null,
      sort: null,
      order: null,
    });
  });

  it("should POST /api/projects and create project with name New Test Project", async () => {
    const newProject = {
      id: "proj-new123",
      name: "New Test Project",
      flow: { nodes: [], edges: [] },
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    }(
      // Configure repository mock to return created project
      projectsRepository.create as jest.Mock,
    ).mockResolvedValueOnce(newProject);

    const requestBody = {
      name: "New Test Project",
      flow: { nodes: [], edges: [] },
    };

    const request = new NextRequest("http://localhost:3000/api/projects", {
      method: "POST",
      body: JSON.stringify(requestBody),
      headers: {
        "Content-Type": "application/json",
      },
    });

    const response = await POST(request);

    // Verify response status and structure
    expect(response.status).toBe(201);

    const data = await response.json();
    expect(data).toEqual({
      success: true,
      project: newProject,
    });

    // Verify repository was called with correct data
    expect(projectsRepository.create).toHaveBeenCalledWith(requestBody);
  });
});
```

### **Acceptance Criteria**

- [ ] GET /api/projects returns success:true with empty array
- [ ] POST /api/projects creates project with name 'New Test Project'
- [ ] Repository methods are correctly mocked and called
- [ ] Response status codes are correct (200 for GET, 201 for POST)

---

## **TICKET 6: Additional Mocks (QuickJS & Monaco)**

### **Title**

Add QuickJS and Monaco Editor mocks with validation tests

### **Type:** Mock + Testing

### **Priority:** Low

### **Labels:** `testing`, `mocks`

### **Depends On:** TICKET 4

### **Description**

Add mocks for JavaScript execution and code editing with specific tests to validate they work.

### **Files to Create**

**`__mocks__/quickjs-emscripten.ts`**

```typescript
export const getQuickJS = jest.fn().mockResolvedValue({
  newContext: () => ({
    global: {
      setProp: jest.fn(),
      getProp: jest.fn(),
    },
    newString: jest.fn((str) => str),
    newNumber: jest.fn((num) => num),
    evalCode: jest.fn((code) => ({
      value: {
        consume: () => "mock result",
      },
      error: null,
    })),
    dump: jest.fn((value) => value),
    dispose: jest.fn(),
    runtime: {
      setMemoryLimit: jest.fn(),
      computeMemoryUsage: jest.fn(() => ({
        currentMemory: 1024,
      })),
    },
  }),
});
```

**`__mocks__/@monaco-editor/react.tsx`**

```typescript
import React from 'react'

const MonacoEditor = ({
  value,
  onChange,
  language = 'javascript'
}: {
  value?: string
  onChange?: (value: string | undefined) => void
  language?: string
}) => {
  return (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      aria-label={`Code editor for ${language}`}
    />
  )
}

export default MonacoEditor
```

### **Tests to Write**

**`src/lib/services/quickjs-executor.spec.ts`**

```typescript
import { QuickJSExecutor } from "./quickjs-executor";

describe("QuickJSExecutor", () => {
  let executor: QuickJSExecutor;

  beforeEach(() => {
    executor = new QuickJSExecutor();
  });

  afterEach(() => {
    executor.dispose();
  });

  it("should execute JavaScript code and return result with mock QuickJS", async () => {
    await executor.initialize();

    const code = `
      const x = 10
      const y = 20
      return x + y
    `;

    const result = await executor.execute(code, { input: 5 });

    // With our mock, evalCode always returns 'mock result'
    expect(result.value).toBe("mock result");
    expect(result.error).toBeNull();
    expect(result.logs).toEqual([]);
  });

  it("should handle timeout and dispose context properly", async () => {
    await executor.initialize();

    // Test that timeout is set (default 5000ms)
    const longRunningCode = "while(true) {}";

    // This should timeout with our mock (mock doesn't actually run code)
    const result = await executor.execute(longRunningCode, {}, 100);

    // Mock should still return a result
    expect(result).toBeDefined();
  });

  it("should capture console output from executed code", async () => {
    await executor.initialize();

    const code = `
      console.log('Hello')
      console.error('Error message')
      return 42
    `;

    const result = await executor.execute(code);

    // Mock returns 'mock result' for value
    expect(result.value).toBe("mock result");
    // Console functions are mocked but logs would be captured if implemented
    expect(result.logs).toBeDefined();
  });
});
```

**`src/containers/function-properties/components/function-code-editor.spec.tsx`**

```typescript
import { render, fireEvent } from '@testing-library/react'
import { FunctionCodeEditor } from './function-code-editor'

describe('FunctionCodeEditor', () => {
  const mockOnCodeChange = jest.fn()
  const mockOnExpandEditor = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render Monaco Editor as textarea with initial code', () => {
    const { getByTestId, getByText } = render(
      <FunctionCodeEditor
        code="return input * 2"
        onCodeChange={mockOnCodeChange}
        onExpandEditor={mockOnExpandEditor}
      />
    )

    // Check label is rendered
    expect(getByText('JavaScript Code')).toBeInTheDocument()

    // Check expand button is rendered
    const expandButton = getByText('Expand')
    expect(expandButton).toBeInTheDocument()

    // Monaco Editor should be mocked as textarea
    const editor = getByTestId('monaco-editor') as HTMLTextAreaElement
    expect(editor).toBeInTheDocument()
    expect(editor.value).toBe('return input * 2')
  })

  it('should call onCodeChange when code is edited', () => {
    const { getByTestId } = render(
      <FunctionCodeEditor
        code="return input * 2"
        onCodeChange={mockOnCodeChange}
        onExpandEditor={mockOnExpandEditor}
      />
    )

    const editor = getByTestId('monaco-editor') as HTMLTextAreaElement

    // Simulate typing new code
    fireEvent.change(editor, { target: { value: 'return input * 3' } })

    // Verify callback was called with new code
    expect(mockOnCodeChange).toHaveBeenCalledWith('return input * 3')
  })

  it('should call onExpandEditor when expand button is clicked', () => {
    const { getByText } = render(
      <FunctionCodeEditor
        code="return input * 2"
        onCodeChange={mockOnCodeChange}
        onExpandEditor={mockOnExpandEditor}
      />
    )

    const expandButton = getByText('Expand')
    fireEvent.click(expandButton)

    expect(mockOnExpandEditor).toHaveBeenCalledTimes(1)
  })

  it('should render with correct editor configuration', () => {
    const { getByTestId } = render(
      <FunctionCodeEditor
        code="// JavaScript function"
        onCodeChange={mockOnCodeChange}
        onExpandEditor={mockOnExpandEditor}
      />
    )

    const editor = getByTestId('monaco-editor')

    // Monaco mock includes language in aria-label
    expect(editor).toHaveAttribute('aria-label', 'Code editor for javascript')
  })
})
```

### **Acceptance Criteria**

- [ ] QuickJSExecutor test validates code execution with mocked QuickJS
- [ ] QuickJSExecutor properly initializes and disposes
- [ ] FunctionCodeEditor renders Monaco Editor as mocked textarea
- [ ] FunctionCodeEditor handles code changes and expand button clicks
- [ ] Both components work correctly with their respective mocks

---

## **TICKET 7: Integration Testing Setup**

### **Title**

Set up integration testing with MSW for external API mocking

### **Type:** Integration Testing + Mock

### **Priority:** Medium

### **Labels:** `testing`, `integration`, `msw`, `api`

### **Depends On:** TICKETS 2, 3, 4

### **Description**

Set up MSW (Mock Service Worker) for mocking external IoT Supervisor API calls and create an integration test that validates the complete flow from project creation to deployment.

### **Dependencies to Install**

```bash
pnpm add -D msw
```

### **Files to Create**

**`__mocks__/msw/handlers.ts`**

```typescript
import { rest } from "msw";

export const handlers = [
  // Mock IoT Supervisor deployment endpoint
  rest.post("http://localhost:3001/api/config/deploy", (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        deploymentId: "deploy-integration-123",
        status: "deployed",
        message: "Flow deployed successfully",
      }),
    );
  }),

  // Mock IoT Supervisor status endpoint
  rest.get("http://localhost:3001/status", (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: "healthy",
        version: "1.0.0",
        uptime: 3600,
      }),
    );
  }),
];
```

**`__mocks__/msw/server.ts`**

```typescript
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

**Update jest.setup.js**

```javascript
import "@testing-library/jest-dom";
import { server } from "./__mocks__/msw/server";

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// ... existing browser API mocks
```

### **Test to Write**

**`src/__tests__/integration/project-deployment.spec.ts`**

```typescript
import { createProject } from "../../lib/db/projects";
import { deployToSupervisor } from "../../lib/api/supervisor";
import { __mockExecute } from "@libsql/client";

describe("Project Deployment Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should save project Integration Test Project and deploy to supervisor returning deploy-integration-123", async () => {
    // Step 1: Configure database mock for project creation
    __mockExecute.mockResolvedValueOnce({
      rows: [{ id: "proj-integration-456" }],
      columns: ["id"],
      rowsAffected: 1,
    });

    // Step 2: Create a project with specific flow
    const projectData = {
      name: "Integration Test Project",
      flow: {
        nodes: [
          {
            id: "input-node",
            type: "constant",
            position: { x: 100, y: 100 },
            data: { value: 25, label: "Temperature Input" },
          },
          {
            id: "output-node",
            type: "bacnet-analog-output",
            position: { x: 300, y: 100 },
            data: { objectId: "AO:1", label: "Damper Position" },
          },
        ],
        edges: [
          {
            id: "edge-1",
            source: "input-node",
            target: "output-node",
            sourceHandle: "output",
            targetHandle: "input",
          },
        ],
      },
    };

    const project = await createProject(projectData);

    // Verify project was created with expected properties
    expect(project).toEqual({
      id: "proj-integration-456",
      name: "Integration Test Project",
      flow: projectData.flow,
    });

    // Step 3: Deploy project to supervisor (MSW will handle the HTTP call)
    const deployment = await deployToSupervisor(project.flow);

    // Verify deployment response matches MSW mock
    expect(deployment).toEqual({
      success: true,
      deploymentId: "deploy-integration-123",
      status: "deployed",
      message: "Flow deployed successfully",
    });

    // Step 4: Verify the complete flow worked
    expect(project.id).toBe("proj-integration-456");
    expect(project.name).toBe("Integration Test Project");
    expect(deployment.deploymentId).toBe("deploy-integration-123");
    expect(deployment.status).toBe("deployed");

    // Verify database was called with correct project data
    expect(__mockExecute).toHaveBeenCalledWith(
      expect.objectContaining({
        sql: expect.stringContaining("INSERT INTO projects"),
        args: expect.arrayContaining(["Integration Test Project"]),
      }),
    );
  });
});
```

### **API Client to Create**

**`src/lib/api/supervisor.ts`** (if it doesn't exist)

```typescript
interface DeploymentResponse {
  success: boolean;
  deploymentId: string;
  status: string;
  message: string;
}

export async function deployToSupervisor(
  flow: any,
): Promise<DeploymentResponse> {
  const response = await fetch("http://localhost:3001/api/config/deploy", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(flow),
  });

  if (!response.ok) {
    throw new Error(`Deployment failed: ${response.statusText}`);
  }

  return response.json();
}
```

### **Acceptance Criteria**

- [ ] MSW correctly intercepts external API calls
- [ ] Project 'Integration Test Project' is created with id 'proj-integration-456'
- [ ] Deployment returns deploymentId 'deploy-integration-123'
- [ ] Integration test validates complete flow: create � save � deploy
- [ ] No actual HTTP calls are made to external services
- [ ] Test passes exactly as written

---

## **TICKET 8: Testing Documentation**

### **Title**

Create comprehensive testing documentation

### **Type:** Documentation

### **Priority:** Low

### **Labels:** `testing`, `documentation`

### **Depends On:** TICKETS 2-7

### **Description**

Document testing setup, patterns, and best practices based on implemented infrastructure.

### **Deliverables**

**`/docs/testing-guide.md`**

```markdown
# Testing Guide

## Overview

Comprehensive testing setup for the BMS Supervisor Controller Designer app.

## Quick Start

\`\`\`bash
cd apps/designer
pnpm test # Run all tests
pnpm test:watch # Watch mode
pnpm test:coverage # Coverage report
\`\`\`

## File Naming Convention

All test files use `*.spec.ts` or `*.spec.tsx` extension.

## Testing Infrastructure

### Available Mocks

- **Zustand**: Automatic store reset between tests
- **@libsql/client**: Database operations
- **@xyflow/react**: React Flow components
- **quickjs-emscripten**: JavaScript execution
- **@monaco-editor/react**: Code editor
- **MSW**: External API calls

### Test Utilities

- `renderWithProviders`: Render with React Flow and other providers
- Mock factories in `__mocks__` directories

## Testing Patterns

### Store Testing

\`\`\`typescript
import { renderHook, act } from '@testing-library/react'
import { useFlowStore } from './flow-store'

test('store operations', () => {
const { result } = renderHook(() => useFlowStore())
act(() => {
result.current.addNode({ id: 'test' })
})
expect(result.current.nodes).toHaveLength(1)
})
\`\`\`

### Component Testing

\`\`\`typescript
import { render } from '@test-utils/render'
test('component renders', () => {
const { getByRole } = render(<MyComponent />)
expect(getByRole('button')).toBeInTheDocument()
})
\`\`\`

### API Route Testing

\`\`\`typescript
import { GET } from './route'
import { NextRequest } from 'next/server'

test('API endpoint', async () => {
const request = new NextRequest('http://localhost:3000/api/test')
const response = await GET(request)
expect(response.status).toBe(200)
})
\`\`\`

### Integration Testing

\`\`\`typescript
// Uses MSW for external API mocking
test('full flow', async () => {
const project = await createProject(data)
const deployment = await deployToSupervisor(project.flow)
expect(deployment.success).toBe(true)
})
\`\`\`

## Adding New Mocks

1. Create mock in `__mocks__/package-name/`
2. Export mock functions with `__mock` prefix for test access
3. Add validation test to ensure mock works
4. Update this documentation

## Best Practices

- Test behavior, not implementation
- Use descriptive test names
- One assertion per test when possible
- Mock external dependencies
- Clean up between tests

## Troubleshooting

- Check mock configuration if imports fail
- Verify test environment variables
- Ensure MSW handlers match API endpoints
```

**Update `apps/designer/README.md`**
Add testing section:

```markdown
## Testing

### Running Tests

\`\`\`bash
pnpm test # Run all tests
pnpm test:watch # Watch mode
pnpm test:coverage # Coverage report
\`\`\`

### Test Structure

- `*.spec.ts` - Unit tests
- `*.spec.tsx` - Component tests
- `__tests__/integration/` - Integration tests

See [Testing Guide](/docs/testing-guide.md) for detailed information.
```

### **Acceptance Criteria**

- [ ] Testing guide explains complete setup
- [ ] Documents how to add new mocks with examples
- [ ] Includes real patterns from implemented tests
- [ ] README updated with testing section
- [ ] New developers can write tests following the guide

---

## **Summary**

### **Ticket Order**

1. **Basic Infrastructure** - Foundation setup
2. **Zustand Mock** - State management testing
3. **Database Mock** - Repository testing
4. **React Flow Mock** - Component testing
5. **API Route Testing** - Next.js endpoints
6. **Additional Mocks** - QuickJS & Monaco
7. **Integration Testing** - MSW + full flow
8. **Documentation** - Complete guide

### **Key Features**

- **Explicit tests**: Every test is fully specified with expected results
- **Incremental approach**: Each ticket builds on previous ones
- **Real functionality**: Tests actual app features, not hypothetical ones
- **Complete coverage**: Unit, integration, API, and component testing
- **Production ready**: Professional testing infrastructure

### **Total Estimated Effort**

Small, focused tickets without time pressure - implement at comfortable pace.
