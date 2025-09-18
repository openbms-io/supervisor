# BMS Supervisor Controller - Claude Context

## Project Overview

Visual programming platform for building management systems with IoT device integration.

**Architecture Flow**: Designer (Visual Programming) → Schema (Communication Protocol) → IoT Supervisor (Execution Engine)

## Schema Package Purpose

The `bms-schemas` package defines the data format used to send visual programming configurations from the Designer app to the IoT Supervisor for execution on IoT devices.

- **Designer App**: Creates visual flow configurations using drag-and-drop interface
- **Schema Package**: Validates and transforms configurations (Zod → JSON Schema → Pydantic)
- **IoT Supervisor**: Receives validated configurations and executes the control logic

## Development Philosophy

### Core Principles

1. **Test-Driven Development (TDD)**

   - Write tests first, then implement
   - Red-Green-Refactor cycle
   - Tests drive design decisions

2. **DO NOT OVERENGINEER**

   - Simple, direct implementations
   - Avoid premature abstractions
   - Minimal viable solutions that can evolve

3. **Fail Fast**

   - Surface issues immediately
   - Clear error messages
   - Quick feedback loops

4. **Prop Up Issues Faster**

   - Make problems visible quickly
   - Don't hide or suppress errors
   - Enable rapid debugging and resolution

5. **DO NOT ADD COMMENTS**
   - Make the function name and variable names clear enough, so comments are not required
   - Add comments ONLY in special cases to define WHY was something done.
   - Dont add comments for WHAT was done. Use variables and functions for WHAT names.

### TDD Workflow for This Project

#### Schema Development (TDD)

```bash
# 1. Write failing test
cd packages/bms-schemas
# Edit .spec.ts file with new test case

# 2. Run test (should fail)
npm test

# 3. Implement schema to make test pass
# Edit schema .ts file

# 4. Verify test passes
pnpm test

# 5. Regenerate outputs
pnpm run generate
```

#### API Development (TDD)

```bash
# 1. Write failing API test
cd apps/iot-supervisor-app
# Edit test_*.py file

# 2. Run test (should fail)
pytest tests/

# 3. Implement endpoint
# Edit src/main.py

# 4. Verify test passes
pytest tests/

# 5. Test integration
iot-supervisor-app start-serve
```

#### Component Development (TDD)

```bash
# 1. Write failing component test
cd apps/designer
# Edit *.spec.ts file

# 2. Run test (should fail)
pnpm test

# 3. Implement component
# Edit component .tsx file

# 4. Verify test passes
pnpm test
```

## Key Commands

### Quick Start

```bash
# Initial setup
pnpm install
pnpm run schema:generate
pnpm run setup:hooks

# Development
pnpm run dev                    # Start both apps
pnpm run test                   # Run all tests
```

### Schema Workflow

```bash
cd packages/bms-schemas
pnpm test                        # Run schema tests
pnpm run generate               # Generate all outputs
pnpm run test:integration       # E2E schema test
```

### IoT Supervisor Setup

```bash
cd apps/iot-supervisor-app
./install.sh                   # One-time setup
source .venv/bin/activate      # Activate venv
iot-supervisor-app health      # Test CLI
```

### Designer App

```bash
cd apps/designer
pnpm run dev                    # Start on port 3000
pnpm test                       # React component tests
```

## Technology Stack

### Frontend (Designer)

- **Next.js 15.5** with Turbopack
- **TypeScript** with strict type checking
- **shadcn/ui** component library (Radix UI + Tailwind)
- **Tailwind CSS v4** for styling
- **React Flow** for visual programming interface
- **Zustand** for state management
- **Jest + React Testing Library** for testing

### Backend (IoT Supervisor)

- **FastAPI** with automatic OpenAPI docs
- **Typer** for CLI interface
- **uvicorn** ASGI server with hot reload
- **BACnet libraries** (BAC0, bacpypes) for IoT integration
- **pytest** for testing
- **Virtual environment** for isolation

### Schema Pipeline

- **Source**: Zod schemas (TypeScript)
- **Intermediate**: JSON Schema
- **Target**: Pydantic models (Python)
- **Testing**: Jest (TypeScript) + pytest (Python) + E2E integration

## File Structure

```
bms-supervisor-controller/
├── CLAUDE.md                  # This file - project context
├── README.md                  # User documentation
├── docs/coding-standards.md   # Development standards
├── apps/
│   ├── designer/             # Visual programming interface
│   └── iot-supervisor-app/   # Execution engine
└── packages/
    └── bms-schemas/          # Integration schemas
        ├── src/              # Source Zod schemas
        ├── typescript/       # Generated TS (for Designer)
        ├── python/          # Generated Python (for IoT Supervisor)
        └── json-schema/     # Intermediate format
```

## Common Development Tasks

### Adding New Node Type

```bash
# 1. TDD: Write test first
cd packages/bms-schemas
# Add test case to src/nodes/types.spec.ts

# 2. Implement schema
# Add to NodeTypeSchema enum in src/nodes/types.ts

# 3. Regenerate for both apps
pnpm run generate

# 4. Test integration in both apps
cd ../../apps/designer && npm run dev
cd ../iot-supervisor-app && iot-supervisor-app start-serve
```

### Adding New UI Components (shadcn/ui)

```bash
# Install specific component
npx shadcn@latest add <component-name>

# Example: Add form components
npx shadcn@latest add form select switch

# Available components: button, input, card, badge, dialog,
# dropdown-menu, separator, tooltip, form, select, switch, etc.
```

### Package manager

Nodejs -> pnpm
Python -> pip

### Tailwind CSS v4 Compatibility

**Important**: This project uses Tailwind CSS v4 with shadcn/ui. Some compatibility notes:

- Replaced `@apply bg-background text-foreground` with direct CSS properties
- Use `background-color: hsl(var(--background))` instead of `@apply bg-background`
- CSS custom properties (--border, --background, etc.) work fine as hsl() values
- All shadcn/ui components are compatible after CSS adjustments

### Troubleshooting (Fail Fast)

#### Schema Issues

```bash
# Clean and regenerate everything
cd packages/bms-schemas
npm run clean
npm run build                   # Tests + generation
```

#### Import Errors

```bash
# Check if schemas are generated
ls packages/bms-schemas/python/
ls packages/bms-schemas/typescript/

# Regenerate if missing
pnpm run schema:generate
```

#### IoT Supervisor Import Issues

```bash
cd apps/iot-supervisor-app
source .venv/bin/activate
python -c "from python.flow_node import FlowNode; print('Import OK')"
```

## Integration Points

### Designer → IoT Supervisor

1. **Designer** creates FlowNode configurations
2. **Schema** validates and serializes to JSON
3. **API call** sends JSON to IoT Supervisor `/api/config/deploy`
4. **IoT Supervisor** deserializes using Pydantic models
5. **Execution engine** runs the configuration

### Testing Integration

```bash
# Start both apps
pnpm run dev

# Run E2E test
cd packages/bms-schemas
npm run test:integration
```

## Zustand gotcha

- Subscribe to specific values in zustand store for nested objects. e.g below:

  const valueType = useFlowStore(state => {
  onst node = state.nodes.find(n => n.id === id)
  const nodeData = node?.data
  return nodeData?.metadata?.valueType ?? nodeData?.valueType ?? 'number' as ValueType
  })

  const label = useFlowStore(state => {
  const node = state.nodes.find(n => n.id === id)
  const nodeData = node?.data
  return nodeData?.label ?? 'Constant'
  })

## Development Mindset

- **Write tests first** - they define the expected behavior
- **Keep it simple** - avoid complex abstractions until needed
- **Make errors obvious** - don't hide problems
- **Quick iterations** - fast test-code-test cycles
- **Schema-driven** - changes start with schema tests, then implementation
- **Use existing components** - prefer shadcn/ui components over custom implementations
- **Define Types** - Dont use any or unknown. Define types where it cannot be inferred. But, dont fallback to using any or unknown.
- **Coding Conventions** - Follow coding conventions listed in docs/coding-standards.md
- **Bug Fix** - Always focus on finding and assessing root cause first. Present your plan, before provising a fix with options.
