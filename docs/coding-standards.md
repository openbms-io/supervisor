# Coding Standards

This document outlines the coding standards and conventions for the BMS Supervisor Controller project, covering both Python and TypeScript codebases.

## Core Principles

1. **Readability counts**: Code is read more often than it is written
2. **Consistency**: Follow existing patterns in the codebase
3. **Simplicity**: Explicit is better than implicit
4. **Documentation**: Code should be self-documenting with clear naming

## Python Coding Standards

### Primary References

- **PEP 8**: [Official Python Style Guide](https://peps.python.org/pep-0008/)
- **Google Python Style Guide**: [Google's conventions](https://google.github.io/styleguide/pyguide.html)

### Key Conventions

#### Naming Conventions

```python
# Variables and functions: snake_case
user_name = "John"
def calculate_average(numbers):
    pass

# Classes: PascalCase
class DataProcessor:
    pass

# Constants: UPPER_CASE
MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30

# Private methods/variables: leading underscore
_internal_counter = 0
def _private_method():
    pass
```

#### Code Layout

```python
# Indentation: 4 spaces (never tabs)
def function():
    if condition:
        do_something()

# Line length: 79 characters (88 for Black formatter)
# Blank lines: 2 before class/function, 1 between methods

# Imports: Grouped and ordered
import os
import sys

import numpy as np
import pandas as pd

from mypackage import mymodule
from .local import module
```

#### Type Hints (Python 3.5+)

```python
def process_data(items: list[str], count: int = 10) -> dict[str, int]:
    """Process items and return frequency count."""
    return {}
```

#### Docstrings

```python
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Tools & Configuration

#### Required Tools

- **Black**: Code formatter (line length: 88)
- **Ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **mypy**: Static type checker

#### Configuration Files

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

## TypeScript Coding Standards

### Primary References

- **Google TypeScript Style Guide**: [Official guide](https://google.github.io/styleguide/tsguide.html)
- **TypeScript Handbook**: [Best practices](https://www.typescriptlang.org/docs/handbook/intro.html)

### Key Conventions

#### Naming Conventions

```typescript
// Variables and functions: camelCase
const userName = "John";
function calculateAverage(numbers: number[]): number {
  return 0;
}

// Classes and interfaces: PascalCase
class DataProcessor {
  private data: string[];
}

interface UserConfig {
  name: string;
  age: number;
}

// Constants: UPPER_CASE
const MAX_CONNECTIONS = 100;
const DEFAULT_TIMEOUT = 30;

// Type parameters: T prefix + descriptive name
function map<TInput, TOutput>(items: TInput[]): TOutput[] {
  return [];
}

// Booleans: is/has prefix
const isDisabled = true;
const hasPermission = false;
```

#### Type System Best Practices

```typescript
// Prefer interfaces over type aliases for objects
interface User {
  id: string;
  name: string;
}

// Use explicit return types
function getUser(id: string): User | undefined {
  return undefined;
}

// Avoid any - use unknown or specific types
function processData(data: unknown): void {
  // Type guard
  if (typeof data === "string") {
    console.log(data.toUpperCase());
  }
}

// Use readonly for immutability
interface Config {
  readonly apiUrl: string;
  readonly timeout: number;
}
```

#### Async/Await Pattern

```typescript
// Always use async/await over promises
async function fetchData(): Promise<Data> {
  try {
    const response = await fetch("/api/data");
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch data:", error);
    throw error;
  }
}
```

#### Module Organization

```typescript
// Imports: Grouped and ordered
// 1. External libraries
import React from "react";
import { useState, useEffect } from "react";

// 2. Internal absolute imports
import { UserService } from "@/services/user";

// 3. Relative imports
import { Button } from "./components/Button";
import type { ButtonProps } from "./components/Button.types";

// Export at the end of file
export { MyComponent };
export type { MyComponentProps };
```

### Tools & Configuration

#### Required Tools

- **TypeScript**: Type checking and compilation
- **ESLint**: Code quality and standards enforcement
- **Prettier**: Code formatting

#### Configuration Files

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  rules: {
    '@typescript-eslint/explicit-return-type': 'error',
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/no-explicit-any': 'error'
  }
};

// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

## Common Principles Across Languages

### Comments and Documentation

- Write self-documenting code with clear naming
- Comments should explain "why", not "what"
- Keep comments up-to-date with code changes
- Document complex algorithms and business logic

### Error Handling

- Handle errors explicitly, don't suppress them
- Log errors with context for debugging
- Fail fast with clear error messages
- Use custom error types when appropriate

### Testing Conventions

```python
# Python: test_*.py or *_test.py
def test_calculate_average():
    assert calculate_average([1, 2, 3]) == 2
```

```typescript
// TypeScript: *.spec.ts or *.test.ts
describe("calculateAverage", () => {
  it("should return correct average", () => {
    expect(calculateAverage([1, 2, 3])).toBe(2);
  });
});
```

## Project-Specific Rules

### File Organization

- Keep files small and focused (< 300 lines)
- One class/component per file
- Group related functionality in directories
- Use index files for clean exports

### Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports
4. Relative imports

### Git Commit Messages

- Use conventional commits format
- Present tense ("Add feature" not "Added feature")
- Limit subject line to 50 characters
- Reference issue numbers when applicable

## Tools Setup

### VS Code Extensions

- **Python**: Python, Pylance, Black Formatter
- **TypeScript**: ESLint, Prettier, TypeScript Hero
- **Common**: GitLens, Error Lens, Better Comments

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-eslint
    hooks:
      - id: eslint
  - repo: https://github.com/pre-commit/mirrors-prettier
    hooks:
      - id: prettier
```

## References

### Python

- [PEP 8 - Style Guide for Python](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black - The Uncompromising Code Formatter](https://black.readthedocs.io/)
- [Ruff - An extremely fast Python linter](https://github.com/charliermarsh/ruff)

### TypeScript

- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [ESLint Rules](https://eslint.org/docs/rules/)
- [Prettier Options](https://prettier.io/docs/en/options.html)

### General

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [The Twelve-Factor App](https://12factor.net/)
