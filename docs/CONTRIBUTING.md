# Contributing to BMS Supervisor Controller

Thank you for your interest in contributing to BMS Supervisor Controller! This project is a visual programming platform for building management systems with IoT device integration.

## 🎯 How You Can Help

We're actively seeking contributions in several key areas:

### High Priority Areas

1. **Supervisor Engine Core** (`packages/supervisor-engine`)

   - Runtime graph and node registry/evaluators
   - Deterministic scheduler (monotonic clock, drift-corrected)
   - I/O adapter for IoT Service (HTTP/WS; batching, debouncing, COV-first)
   - Bundle format/versioning/validation; preview execution utilities

2. **Headless Engine App** (`apps/headless-engine`)

   - Thin wrapper (CLI + local control API): deploy/reload/status/health
   - Atomic bundle management (staging → activate → rollback)
   - Health/readiness endpoints, structured logs

3. **BACnet Integration** (Phase 7) — `apps/iot-supervisor-app`

   - Real BACnet device discovery
   - Network scanning and enumeration
   - BAC0 (GPL-3.0) integration or bacpypes3 (MIT) alternative

4. **Testing & Quality Assurance**

   - End-to-end and soak tests (timing, drift, network flaps)
   - Performance testing with large node graphs
   - Cross-platform/browser compatibility testing
   - Testing with real bacnet/ip controllers

5. **Documentation**
   - User guides and tutorials
   - API contracts (Engine control, IoT Service)
   - Deployment and setup guides (AGPL source link, release artifacts)

### Medium Priority Areas

1. **UI/UX Enhancements**

   - Canvas interaction improvements
   - Node design and usability
   - Mobile responsiveness

2. **DevOps & Infrastructure**
   - Docker containerization
   - CI/CD pipeline implementation
   - Deployment automation

## 🚀 Setup

For prerequisites and full environment setup (install, dev servers, schema generation), follow the root README:

- See README.md → Quick Start and Development sections
- Optional: run `pnpm run setup:hooks` to enable pre-commit hooks

### Development Workflow

Our development process follows Test-Driven Development (TDD) principles:

#### For Schema Changes

```bash
cd packages/bms-schemas

# 1. Write failing test
# Edit .spec.ts file with new test case

# 2. Run test (should fail)
npm test

# 3. Implement schema
# Edit schema .ts file

# 4. Verify test passes and regenerate
npm test && pnpm run generate
```

#### For Frontend Components

```bash
cd apps/designer

# 1. Write failing component test
# Edit *.spec.tsx file

# 2. Run test (should fail)
pnpm test

# 3. Implement component
# Edit component .tsx file

# 4. Verify test passes
pnpm test
```

#### For Backend API

```bash
cd apps/iot-supervisor-app

# 1. Write failing API test
# Edit test_*.py file

# 2. Run test (should fail)
pytest tests/

# 3. Implement endpoint
# Edit src/main.py

# 4. Verify test passes
pytest tests/
```

## 📋 Project Structure

```
bms-supervisor-controller/
├── apps/
│   ├── designer/             # Next.js visual programming interface
│   ├── headless-engine/      # Node service (engine wrapper; planned)
│   └── iot-supervisor-app/   # FastAPI IoT runtime (BACnet)
├── packages/
│   ├── supervisor-engine/    # Shared runtime engine core
│   └── bms-schemas/          # Shared schema validation
├── docs/                     # Documentation
└── specs/                    # Technical specifications
```

## 🎨 Code Style and Standards

### Code Style Guidelines

Follow the existing code style documented in [docs/coding-standards.md](coding-standards.md).

### Key Principles

1. **Test-Driven Development (TDD)**

   - Write tests first, then implement
   - Red-Green-Refactor cycle

2. **Don't Overengineer**

   - Simple, direct implementations
   - Avoid premature abstractions

3. **Fail Fast**
   - Surface issues immediately
   - Clear error messages

### Code Quality Tools

- **TypeScript**: Strict mode enabled
- **ESLint**: For JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **Black**: Python code formatting
- **Ruff**: Python linting
- **Pre-commit hooks**: Automated code quality checks

### Required Commands Before Submitting

```bash
# Lint and format code
pnpm run lint
pnpm run python:format

# Run all tests
pnpm run test

# Build to check for errors
pnpm run build
```

## 🔄 Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes following TDD**

   - Write tests first
   - Implement the feature
   - Ensure all tests pass

3. **Commit with clear messages**

   ```bash
   git commit -m "Add switch node threshold validation

   - Add validation for threshold input values
   - Include error messages for invalid ranges
   - Update tests for edge cases

   🤖 Generated with Claude Code

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

4. **Push and create PR**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **PR Requirements**
   - Clear description of changes
   - Link to relevant issues
   - Screenshots for UI changes
   - All tests passing
   - Code review approval

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Environment Information**

   - OS and version
   - Node.js version
   - Browser (for frontend issues)

2. **Steps to Reproduce**

   - Clear step-by-step instructions
   - Expected vs actual behavior
   - Screenshots or video if helpful

3. **Context**
   - What you were trying to achieve
   - Any error messages
   - Browser console logs

### Feature Requests

For feature requests, please describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives considered
- Impact on existing functionality

## 🧪 Testing Guidelines

### Test Requirements

- All new features must have tests
- Bug fixes must include regression tests
- Maintain or improve test coverage
- Tests should be readable and maintainable

### Test Types

1. **Unit Tests**

   - Individual functions and components
   - Schema validation
   - Business logic

2. **Integration Tests**

   - API endpoints
   - Database operations
   - Cross-component interactions

3. **E2E Tests**
   - User workflows
   - Canvas operations
   - Full system integration

### Running Tests

```bash
# All tests
pnpm run test

# Specific packages
pnpm --filter designer test
pnpm --filter bms-schemas test
pnpm --filter iot-supervisor-app pytest tests/

# Watch mode for development
pnpm --filter designer test --watch
```

## 📚 Documentation Standards

### Code Documentation

- Use JSDoc for TypeScript functions
- Add docstrings for Python functions
- Comment complex business logic
- Update README files when needed

### User Documentation

- Write clear, beginner-friendly guides
- Include code examples
- Add screenshots for UI features
- Test documentation accuracy

## 🤝 Community Guidelines

### Communication

- Be respectful and inclusive
- Ask questions in GitHub Discussions
- Use clear, descriptive issue titles
- Provide context and examples

### Getting Help

- Check existing issues and documentation
- Ask in GitHub Discussions for general questions
- Tag maintainers for urgent issues only
- Be patient with response times

## 🏆 Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- Project documentation
- GitHub contributor graphs

## 📞 Contact

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community discussion
- **Email**: support@openbms.io

## 📄 License

By contributing to BMS Supervisor Controller, you agree that your contributions will be licensed under the AGPL-3.0 License.

---

**Current Project Status**: Phase 6/8 (In Progress)
**See**: [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed progress tracking

Thank you for contributing to BMS Supervisor Controller! 🎉
