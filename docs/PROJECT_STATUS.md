# Project Status

## Current Phase: 6/8 (In Progress)

[![Phase](https://img.shields.io/badge/Phase-6%2F8-yellow.svg)](docs/PROJECT_STATUS.md)
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

### 🚧 Phase 6: Persistence & Integration (In Progress)

- **Status**: 75% Complete
- **Target**: Oct 2025
- **Completed Features**:
  - SQLite/Turso database integration
  - Project save/load functionality
  - Schema validation pipeline (Zod → JSON Schema → Pydantic)
  - Basic IoT Supervisor integration
- **In Progress**:
  - Edge connection refinements
  - Control flow node edge states (active/inactive visualization)
  - Project deployment to IoT Supervisor
  - Database migration improvements
  - Add below visual programming blocks
    - Timer Node
      - Time-based operations (delays, pulse, on/off delay)
    - Schedule Node
      - Schedule evaluation (weekly, daily, exception schedules)
      - Takes time input, schedule config
      - Outputs active/inactive state
- **Remaining**:
  - Robust error handling for deployment
  - Advanced project management features

### 📋 Phase 7: BACnet Discovery Implementation (Planned)

- **Status**: Not Started
- **Target**: Nov 2025
- **Planned Features**:
  - Real BACnet device discovery
  - Network scanning and device enumeration
  - Point property reading with progress tracking
  - Controller configuration management
  - Discovery error handling and retry logic

### Phase 8: IOT Deployment

- **Status**: Not Started
- **Target**: Dec 2025
- ## **Planned Features**:

### 📋 Phase 9: Supervisor Management (Deferred)

- **Status**: Deferred
- **Target**: -
- **Planned Features**:
  - Multi-supervisor management
  - Supervisor health monitoring
  - Configuration deployment across supervisors
  - Load balancing and failover

## Current Development Focus

### 🎯 Active Work (October 2025)

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

## Contributing Areas

### High Priority Help Needed

1. **BACnet Integration** (Phase 7)

   - Real device discovery implementation
   - BACnet protocol expertise
   - Network scanning optimization

2. **Testing & Quality Assurance**

   - End-to-end testing scenarios
   - Performance testing with large graphs
   - Cross-browser compatibility

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines and development setup instructions.

## Roadmap

### Short Term (Q4 2025)

- Complete Phase 6 (Persistence & Integration)
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

**Last Updated**: October 2025
**Next Review**: November 2025

For questions about the project status or to contribute, see [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue on GitHub.
