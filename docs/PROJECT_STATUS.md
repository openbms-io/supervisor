# Project Status

## Current Phase: 7/11 (In Progress)

[![Phase](https://img.shields.io/badge/Phase-7%2F11-yellow.svg)](docs/PROJECT_STATUS.md)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](docs/PROJECT_STATUS.md)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](docs/LICENSE.md)

**BMS Supervisor Controller** is a visual programming platform for building management systems with IoT device integration. This document tracks the project's development progress and current status.

## Phase Progress Overview

### ✅ Phase 1: Application Shell & BMS Infrastructure UI (Complete)

- **Status**: Complete
- **Completed**: Sept 2025
- **Features**:
  - Next.js 15.5 application shell
  - Tailwind CSS v4 styling system
  - shadcn/ui component library integration
  - Basic layout and navigation structure

### ✅ Phase 2: BMS Infrastructure Management (Complete)

- **Status**: Complete
- **Completed**: Sept 2025
- **Features**:
  - Controller discovery UI framework
  - Mock BACnet data integration
  - Infrastructure tree navigation
  - Point details and metadata display

### ✅ Phase 3: Visual Programming Canvas (Complete)

- **Status**: Complete
- **Completed**: Sept 2025
- **Features**:
  - React Flow integration
  - Drag-and-drop node creation
  - Visual connection system
  - Canvas controls and navigation
  - BACnet node components

### ✅ Phase 4: Canvas Controls & Node Management (Complete)

- **Status**: Complete
- **Completed**: Sept 2025
- **Features**:
  - Node properties panel
  - Canvas toolbar with run controls
  - Node deletion and management
  - Connection validation
  - Visual feedback system

### ✅ Phase 5: Data Integration (Complete)

- **Status**: Complete
- **Completed**: Sept 2025
- **Features**:
  - DataNode system implementation
  - Node execution engine
  - Value computation and propagation
  - Control flow logic (switch nodes)
  - Real-time graph execution

### ✅ Phase 6: Persistence & Integration (Complete)

- **Status**: Complete
- **Completed**: Sept 2025

> **📊 Live Status Tracking**
>
> For real-time project status and active tickets, visit our **[GitHub Project Board](https://github.com/orgs/openbms-io/projects/1/views/1)**
>
> - View current sprint progress
> - See testing infrastructure tickets (#15-22)
> - Track P0/P1/P2 priorities
> - Find suitable issues for contributors

- **Completed Features**:
  - SQLite/Turso database integration
  - Project save/load functionality
  - Schema validation pipeline (Zod → JSON Schema → Pydantic)
  - Basic IoT Supervisor integration
  - Timer Node for time-based operations (delays, pulse, on/off delay)
  - Schedule Node for schedule evaluation (weekly, daily, exception schedules)
  - Function Node with JavaScript execution environment using QuickJS
  - QuickJS memory management and console function cleanup

### 📋 Phase 7: BACnet Discovery Implementation (Planned)

- **Status**: Not Started
- **Target**: Sept 2025
- **Planned Features**:
  - Real BACnet device discovery
  - Network scanning and device enumeration
  - Point property reading with progress tracking
  - Controller configuration management
  - Discovery error handling and retry logic

### Phase 8: Integrating IOT with designer app.

- **Status**: Not Started
- **Target**: Nov 2025
- **Planned Features**:
  - Robust error handling for config deployment from designer app to iot.
  - TBD.

### Phase 9: Turing completeness

- **Status**: Not Started
- **Target**: Nov 2025
- **Planned Features**:
  - Edge connection refinements
  - Turing Completeness features:
    - Memory/Register node for holding mutable state across execution steps
    - Variable Set/Get nodes for named variable store in runtime context
    - While loop node (or Repeat-Until) for iterative control flow
    - Boolean logic nodes (NOT, AND, OR) for combinatorial logic operations
    - Delay node (one-tick delay) for breaking instantaneous cycles in feedback loops

### Phase 10: IOT Deployment

- **Status**: Not Started
- **Target**: Dec 2025
- **Planned Features**:
  - Project deployment to IoT Supervisor

### Phase 11: Advanced Project Management

- **Status**: Not Started
- **Target**: TBD
- **Planned Features**:
  - Advanced project management features

### 📋 Phase 12: Supervisor Management (Deferred)

- **Status**: Deferred
- **Target**: -
- **Planned Features**:
  - Multi-supervisor management
  - Supervisor health monitoring
  - Configuration deployment across supervisors
  - Load balancing and failover

## Current Development Focus

### 🎯 Active Work (September 2025)

1. **Edge Connection System**

   - Custom edge rendering with BaseEdge component
   - Active/inactive state visualization for control flow
   - Edge type management and validation
   - Connection blocking issue resolution

2. **Control Flow Nodes**

   - Switch node implementation with threshold conditions
   - Reactive state updates using Zustand selectors
   - Handle connection management
   - Input/output value propagation

3. **Type Safety & Build Process**

   - TypeScript strict mode compliance
   - React Flow EdgeTypes compatibility
   - ESLint rule adherence
   - Build pipeline optimization

### 🔧 Recent Achievements

- ✅ Implemented Timer and Schedule nodes for time-based operations (commits 07a8462, 0636473)
- ✅ Added JavaScript function node with QuickJS execution environment (commit e9c68af)
- ✅ Fixed QuickJS memory management issues and console function cleanup (commits 4a2d90e, 8fccda4)
- ✅ Implemented switch nodes with conditional logic (gt, lt, eq, gte, lte)
- ✅ Added custom control-flow edges with active/inactive states
- ✅ Fixed edge connection blocking issues
- ✅ Resolved reactive state updates for node execution
- ✅ TypeScript build compatibility with React Flow EdgeTypes

## Known Issues & Limitations

### Current Limitations

- **Mock Data Only**: Currently using mock BACnet data, real device integration pending Phase 7
- **Single Supervisor**: Multi-supervisor management deferred to Phase 8
- **Basic Persistence**: Project management features are minimal
- **Limited Node Types**: Focus on core nodes (constant, arithmetic, switch)

### Active Bug Fixes

- Edge style rendering compatibility with SVG paths
- Connection handle validation edge cases
- Switch node input value updates requiring manual interaction

### Performance Considerations

- Canvas performance with large node graphs (>100 nodes) not yet tested
- Real-time execution scaling needs evaluation
- Database query optimization for large projects

## Technology Stack Status

### Frontend (Designer App)

- ✅ Next.js 15.5 with Turbopack
- ✅ TypeScript with strict type checking
- ✅ shadcn/ui component library
- ✅ Tailwind CSS v4
- ✅ React Flow for visual programming
- ✅ Zustand for state management
- ✅ Jest + React Testing Library

### Backend (IoT Supervisor)

- ✅ FastAPI with automatic OpenAPI docs
- ✅ Typer CLI interface
- ✅ uvicorn ASGI server
- 🚧 BACnet libraries: BAC0 (GPL-3.0) as primary choice; bacpypes3 (MIT) as alternative — planned for Phase 7
- ✅ pytest testing framework
- ✅ Virtual environment setup

### Schema Pipeline

- ✅ Zod schemas (TypeScript source)
- ✅ JSON Schema generation
- ✅ Pydantic model generation
- ✅ Cross-language validation
- ✅ Integration testing

### Infrastructure

- ✅ PNPM monorepo
- ✅ Pre-commit hooks
- ✅ SQLite (local) + Turso (remote)
- 🚧 Docker containerization (planned)
- 🚧 CI/CD pipeline (planned)

## 🧪 Testing Infrastructure (Perfect for New Contributors!)

**Status**: Testing infrastructure tickets created and available on [GitHub Project Board](https://github.com/orgs/openbms-io/projects/1/views/1)

We've created **8 comprehensive testing tickets** that are perfect entry points for new contributors. Each ticket has detailed specifications, exact code requirements, and clear acceptance criteria.

### High Priority Testing Tickets (P0)

- **[#15: Basic Testing Infrastructure Setup](https://github.com/openbms-io/supervisor/issues/15)** - Foundation setup
- **[#16: Zustand Mock with Flow Store Test](https://github.com/openbms-io/supervisor/issues/16)** - State management testing
- **[#17: Database Mock with Repository Test](https://github.com/openbms-io/supervisor/issues/17)** - Database operations
- **[#18: React Flow Mock with ConstantNode Test](https://github.com/openbms-io/supervisor/issues/18)** - Component testing

### Medium Priority Testing Tickets (P1)

- **[#19: Next.js API Route Testing](https://github.com/openbms-io/supervisor/issues/19)** - API endpoint testing
- **[#21: Integration Testing Setup](https://github.com/openbms-io/supervisor/issues/21)** - End-to-end workflows

### Low Priority Testing Tickets (P2)

- **[#20: Additional Mocks (QuickJS & Monaco)](https://github.com/openbms-io/supervisor/issues/20)** - External library mocking
- **[#22: Testing Documentation](https://github.com/openbms-io/supervisor/issues/22)** - Guide creation

### Why These Tickets Are Great for Contributors

✅ **Self-contained** - Each ticket is independent and well-defined
✅ **Learning opportunities** - Learn Jest, React Testing Library, mocking patterns
✅ **Clear specifications** - Exact code to write with acceptance criteria
✅ **Mentorship available** - Team ready to help first-time contributors
✅ **TDD approach** - Follows our test-driven development philosophy

### Getting Started

1. Visit the [Project Board](https://github.com/orgs/openbms-io/projects/1/views/1) to see current status
2. Pick a ticket that matches your experience level
3. Follow our [Fork & Pull Request Guide](CONTRIBUTING.md#-contributing-via-fork--pull-request)
4. Ask questions in [GitHub Discussions](https://github.com/openbms-io/supervisor/discussions)

## Contributing Areas

### High Priority Help Needed

1. **Testing Infrastructure** ⭐ **Perfect for New Contributors**

   - **8 ready-to-implement tickets** ([#15-22](https://github.com/openbms-io/supervisor/issues?q=is%3Aissue+is%3Aopen+label%3Atesting))
   - Jest, React Testing Library, mocking patterns
   - Clear specifications with acceptance criteria
   - Follow our [Fork & Pull Request Guide](CONTRIBUTING.md#-contributing-via-fork--pull-request)

2. **BACnet Integration** (Phase 7)

   - Real device discovery implementation
   - BACnet protocol expertise
   - Network scanning optimization

3. **Documentation**

   - User guides and tutorials
   - API documentation
   - Deployment guides

### Medium Priority

1. **UI/UX Improvements**

   - Canvas interaction enhancements
   - Node design and usability
   - Mobile responsiveness

2. **DevOps & Infrastructure**

   - Docker containerization
   - CI/CD pipeline setup
   - Deployment automation

### Getting Started

New to open source or this project?

1. **First-time contributors**: Start with our [Fork & Pull Request Guide](CONTRIBUTING.md#-contributing-via-fork--pull-request)
2. **Check the live board**: Visit our [GitHub Project Board](https://github.com/orgs/openbms-io/projects/1/views/1) for current status
3. **Get help**: Join our Discord community at https://discord.gg/SUkvbwkDGz

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines and development setup instructions.

## Roadmap

### Short Term (Q4 2025)

- Complete Phase 6 (Persistence & Integration) - including Turing Completeness features
- Complete Phase 7 (BACnet Discovery)
- Stabilize core visual programming features
- Improve test coverage to >80%
- Add comprehensive documentation

### Medium Term (Q1 2026)

- Complete Phase 8 (Supervisor Management)
- Implement real device integration
- Add advanced node types
- Performance optimization
- Production deployment features

### Long Term (Q2+ 2026)

- Advanced BMS functionality
- Community-driven enhancements

---

**Last Updated**: September 18, 2025
**Next Review**: October 2025

**Recent Updates**:

- ✅ Created 8 comprehensive testing infrastructure tickets (#15-22)
- ✅ Added [GitHub Project Board](https://github.com/orgs/openbms-io/projects/1/views/1) for live tracking
- ✅ Enhanced [CONTRIBUTING.md](CONTRIBUTING.md) with fork & pull request workflow
- ✅ Prioritized testing tickets for new contributor onboarding

For questions about the project status or to contribute, see [CONTRIBUTING.md](CONTRIBUTING.md) or check our [Project Board](https://github.com/orgs/openbms-io/projects/1/views/1).
