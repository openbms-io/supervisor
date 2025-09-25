# BMS Supervisor Controller

[![Phase](https://img.shields.io/badge/Phase-6%2F8-yellow.svg)](docs/PROJECT_STATUS.md)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](docs/PROJECT_STATUS.md)
[![License](https://img.shields.io/badge/License-AGPL-blue.svg)](docs/LICENSE.md)
[![Discord](https://img.shields.io/discord/1417899927304016146)](https://discord.gg/SUkvbwkDGz)

Visual programming platform for building management systems with IoT device integration.
[Live Preview](https://supervisor-designer.vercel.app/projects)

## 📊 Project Status

**Current Phase**: 6/8 (Persistence & Integration) - See [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for detailed progress tracking.

- ✅ **Phases 1-5 Complete**: Core visual programming infrastructure
- 🚧 **Phase 6 In Progress**: Database persistence, project management, edge refinements
- 📋 **Phase 7 Planned**: Real BACnet device discovery and integration
- 📋 **Phase 8 Deferred**: Multi-supervisor management

## 🤝 Contributing

We welcome contributions! This project is in active development and there are many areas where help is needed:

- **BACnet Integration**: Real device discovery and protocol expertise
- **Testing**: End-to-end scenarios and performance testing
- **Documentation**: User guides and API documentation
- **UI/UX**: Canvas improvements and mobile responsiveness

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed contribution guidelines.

## Architecture

This is a **PNPM monorepo** with two main applications and a shared schema package:

- **🎨 Designer App** (`apps/designer/`) - Next.js 15.5 visual programming interface
- **🔧 BMS IoT App** (`apps/bms-iot-app/`) - BACnet/MQTT runtime for IoT devices
- **📋 BMS Schemas** (`packages/bms-schemas/`) - Shared schema validation (Zod → JSON Schema → Pydantic)

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥18.0.0
- **PNPM** ≥9.0.0
- **Python** ≥3.11

### Installation

```bash
# Clone repository with submodules
git clone --recurse-submodules https://github.com/openbms-io/supervisor.git
cd bms-supervisor-controller

# Install all dependencies
pnpm install

# Generate schemas (first time setup)
pnpm run schema:generate
```

### Development

```bash
# Start both apps in development mode
pnpm run dev

# Or start individually:
pnpm --filter designer run dev          # Designer on http://localhost:3000
pnpm bms-iot:run                        # BMS IoT App
```

## 📋 Schema Management

### Schema Development Workflow

1. **Edit schemas** in `packages/bms-schemas/src/`
2. **Run tests** to validate changes: `pnpm --filter bms-schemas test`
3. **Generate outputs** for both apps: `pnpm run schema:generate`
4. **Test integration** in both Designer and IoT Supervisor apps

### Schema Structure

```
packages/bms-schemas/src/
├── version.ts              # Schema versioning system
├── common/
│   ├── position.ts         # PositionSchema + tests
│   └── position.spec.ts
├── nodes/
│   ├── types.ts           # NodeTypeSchema + tests
│   ├── types.spec.ts
│   ├── flow-node.ts       # FlowNodeSchema + tests
│   └── flow-node.spec.ts
└── __tests__/
    └── integration.spec.ts # Cross-schema tests
```

### Adding New Schemas

1. Create new schema file in appropriate directory (`src/common/` or `src/nodes/`)
2. Create corresponding `.spec.ts` test file
3. Add export to `src/index.ts`
4. Update generation scripts if needed
5. Run `pnpm run schema:generate` to update outputs

## 🛠️ Commands

### Root Level Commands

```bash
# Development
pnpm run dev                    # Start all apps in development
pnpm run build                  # Build all apps
pnpm run test                   # Run all tests
pnpm run lint                   # Lint all code
pnpm run clean                  # Clean all build outputs

# Schema Management
pnpm run schema:generate        # Generate schemas for all apps

# Code Formatting (Python)
pnpm run python:format          # Format Python code with black
pnpm run python:lint            # Lint Python code with ruff
pnpm run python:test            # Run Python tests
```

### Designer App Commands

```bash
cd apps/designer

npm run dev                     # Development server (http://localhost:3000)
npm run build                   # Production build
npm run start                   # Start production server
npm run lint                    # ESLint
npm run test                    # Jest + React Testing Library
```

### Designer Database (SQLite local, Turso remote)

- Local development (SQLite file):

  - Uses `better-sqlite3` with `apps/designer/designer.db` when `TURSO_DATABASE_URL` is not set.
  - Run migrations locally:
    - `pnpm --filter designer db:migrate`
  - Start app:
    - `pnpm --filter designer dev`

- Remote (Turso/libSQL, e.g. Vercel):

  - Set env vars in your shell (or CI) when running migrations:
    - `TURSO_DATABASE_URL='libsql://<your-db>.turso.io'`
    - `TURSO_AUTH_TOKEN='<token>'` (if your DB requires it)
  - Run migrations against Turso:
    - `TURSO_DATABASE_URL='…' TURSO_AUTH_TOKEN='…' pnpm --filter designer db:migrate`
  - On Vercel, add the same env vars in Project Settings → Environment Variables. At runtime the app auto‑detects Turso and uses `@libsql/client` with Drizzle.
  - Migrations are not run at runtime in serverless. Run the command above locally (before deploy) or in your CI of choice.

- Notes:
  - The repository methods are async and work with both drivers.
  - Keep API routes on the Node.js runtime (do not set `export const runtime = 'edge'`).
  - The first migration seeds two example projects; you’ll see them after running migrations.

### BMS IoT App Commands

```bash
# Root-level commands (run from repository root):
pnpm bms-iot:help                        # Show all available commands
pnpm bms-iot:run                         # Start main application
pnpm bms-iot:test                        # Run comprehensive test suite (800+ tests)
pnpm bms-iot:test:verbose                # Verbose test output
pnpm bms-iot:mqtt --help                 # MQTT commands
pnpm bms-iot:config --help               # Configuration management

# Or run directly from app directory:
cd apps/bms-iot-app
PYTHONPATH=../.. python -m src.cli --help           # Show all available commands
PYTHONPATH=../.. python -m src.cli run-main         # Start main application
PYTHONPATH=../.. python -m src.cli set-credentials  # Set authentication
```

### BMS Schemas Commands

```bash
cd packages/bms-schemas

# Testing
npm test                        # Run all schema tests
npm run test:watch             # Watch mode testing
npm run test:coverage          # Coverage report
npm run test:integration       # E2E schema integration test

# Schema Generation
npm run generate               # Complete pipeline
npm run generate:json          # Generate JSON Schema only
npm run generate:python        # Generate Pydantic only
npm run build:ts              # Compile TypeScript only

# Maintenance
npm run clean                  # Clean all generated files
```

## 🧪 Testing

### Unit Tests

```bash
# All tests
pnpm run test

# Per package
pnpm --filter designer test           # React component tests
pnpm --filter bms-schemas test        # Schema validation tests
pnpm --filter iot-supervisor-app pytest tests/  # Python API tests
```

### Integration Tests

```bash
# Schema integration (requires IoT Supervisor running on port 8081)
pnpm --filter bms-schemas run test:integration
```

## 📊 Manual Verification Steps

### 1. Schema Pipeline Verification

```bash
# 1. Test schema generation
cd packages/bms-schemas
npm run clean
npm run build                   # Should pass all tests + generate outputs

# 2. Verify outputs exist
ls typescript/                  # Should have organized JS/TS files
ls python/                     # Should have flow_node.py + index.py
ls json-schema/                # Should have flow-node.json
```

### 2. Designer App Verification

```bash
# 1. Start Designer app
cd apps/designer
npm run dev                    # http://localhost:3000

# 2. Verify schema integration
# - Visit http://localhost:3000
# - Check "Schema Integration Test" component displays correctly
# - Should show green "✅ Valid" status
```

### 3. BMS IoT App Verification

```bash
# 1. Test BMS IoT App CLI
pnpm bms-iot:help

# 2. Run comprehensive tests
pnpm bms-iot:test:verbose

# 3. Test main functionality (requires MQTT configuration)
pnpm bms-iot:run
```

### 4. End-to-End Integration

```bash
# 1. Start both apps
# Terminal 1: pnpm --filter designer run dev (port 3000)
# Terminal 2: pnpm bms-iot:run

# 2. Run integration test
cd packages/bms-schemas
npm run test:integration       # Should pass all 3 test phases
```

## 🏗️ Project Structure

```
bms-supervisor-controller/
├── package.json               # Root workspace config
├── pnpm-workspace.yaml       # PNPM workspace definition
├── .npmrc                    # PNPM configuration
├── apps/
│   ├── designer/             # Next.js visual programming interface
│   ├── bms-iot-app/          # BACnet/MQTT IoT runtime
│   └── bacnet-simulator/     # BACnet device simulator (git submodule)
└── packages/
    └── bms-schemas/          # Shared schema package
        ├── src/              # Source Zod schemas (multi-file)
        ├── typescript/       # Generated TypeScript output
        ├── python/          # Generated Pydantic models
        ├── json-schema/     # Generated JSON Schema
        └── integration-tests/ # E2E schema tests
```

## 🔧 Development Workflow

### Typical Development Session

1. **Start development**: `pnpm run dev`
2. **Make schema changes**: Edit files in `packages/bms-schemas/src/`
3. **Test schemas**: `pnpm --filter bms-schemas test`
4. **Regenerate outputs**: `pnpm run schema:generate`
5. **Verify integration**: Both apps should reflect changes automatically

### Adding New Features

1. **Designer changes**: Edit React components in `apps/designer/src/`
2. **BMS IoT App changes**: Edit Python modules in `apps/bms-iot-app/src/`
3. **Schema changes**: Add/modify schemas in `packages/bms-schemas/src/`
4. **Always run tests**: `pnpm run test` before committing

## 🚨 Troubleshooting

### Common Issues

**Schema generation fails**:

```bash
cd packages/bms-schemas
npm run clean && npm run build
```

**Import errors in apps**:

```bash
# Rebuild schema package
pnpm run schema:generate
```

**Test failures**:

```bash
# Check individual test suites
pnpm --filter bms-schemas test
pnpm --filter designer test
```

**TypeScript errors**:

```bash
# Clean and rebuild everything
pnpm run clean
pnpm install
pnpm run schema:generate
pnpm run build
```

## 🔧 Git Hooks Setup

### Pre-commit Hooks

```bash
# One-time setup (after initial installation)
pnpm run setup:hooks          # Install pre-commit and git hooks

# Update hooks periodically
pnpm run hooks:update         # Update hook versions
```

**What the hooks do:**

- **Python**: Black (format), Ruff (lint), type checking
- **TypeScript**: Prettier (format), ESLint (lint)
- **Common**: Remove trailing whitespace, fix line endings, validate YAML/JSON
- **Schema**: Verify schema tests pass when schemas are modified

**Manual testing:**

```bash
pnpm run hooks:run            # Run hooks on all files
```

## 📚 Technologies Used

- **Frontend**: Next.js 15.5, TypeScript, Tailwind CSS v4, React Flow, Zustand
- **Backend**: FastAPI, Typer, uvicorn, BACnet (BAC0, bacpypes)
- **Schema**: Zod (source), JSON Schema (intermediate), Pydantic (Python)
- **Testing**: Jest, React Testing Library, pytest
- **Build**: PNPM workspaces, TypeScript, tsx, datamodel-code-generator
- **Code Quality**: Prettier, ESLint, Black, Ruff, pre-commit hooks

## 📄 License

This project is licensed under the AGPL-3.0 License. See the root `LICENSE` file and [docs/LICENSE.md](docs/LICENSE.md) for third-party notices and details.

## 📚 Documentation

- **[Project Status](docs/PROJECT_STATUS.md)** - Current development phase and progress
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[License](docs/LICENSE.md)** - AGPL-3.0 License and third-party notices
- **[Coding Standards](docs/coding-standards.md)** - Development standards and practices
