# BMS Schemas

Shared schema package for BMS applications. Auto-generates TypeScript and Python models from Zod schema definitions.

## Schema Pipeline

1. **Zod Schemas** (`src/schemas.ts`) - Source of truth
2. **JSON Schema** (`json-schema/`) - Generated from Zod
3. **Python Models** (`python/bms_schemas/`) - Generated from JSON Schema

## Usage

```bash
# Generate all schemas
npm run generate

# Individual steps
npm run build:ts        # Compile TypeScript
npm run generate:json   # Generate JSON Schema
npm run generate:python # Generate Pydantic models
```

## Python Package

```python
from bms_schemas import FlowNode

# Use generated Pydantic models
```
