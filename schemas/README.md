# Protocol Schema System

This directory contains the **single source of truth** for all WebSocket commands and events in the Saga VTT protocol.

## Overview

Instead of manually maintaining type definitions in both TypeScript and Python, we define the protocol once in JSON Schema and automatically generate type-safe code for both languages.

### Benefits

1. **Single Source of Truth**: Protocol defined once in `protocol.json`
2. **Type Safety**: Compile-time guarantees in both TypeScript and Python
3. **No Drift**: Frontend and backend are guaranteed to match
4. **Self-Documenting**: Schema serves as the protocol specification
5. **Impossible to Forget Fields**: Compilers catch missing fields automatically

## Files

```
schemas/
├── README.md           # This file
└── protocol.json       # Single source of truth for protocol
```

## Generated Files

When you run the generators, these files are created:

- **TypeScript**: `apps/web/src/protocol.generated.ts`
- **Python**: `services/api/app/protocol_generated.py`

**IMPORTANT**: Never edit generated files directly! They will be overwritten.

## Usage

### Generating Types

**TypeScript** (auto-runs before build):
```bash
cd apps/web
pnpm generate-types
```

**Python**:
```bash
python3 tools/generate_types.py
```

### Adding a New Command

1. Edit `schemas/protocol.json`
2. Add your command under the `"commands"` section:

```json
{
  "commands": {
    "MY_NEW_COMMAND": {
      "payload": {
        "type": "object",
        "required": ["field1", "field2"],
        "properties": {
          "field1": {"type": "string"},
          "field2": {"type": "integer"}
        },
        "additionalProperties": false
      }
    }
  }
}
```

3. Regenerate types:
```bash
# TypeScript
cd apps/web && pnpm generate-types

# Python
python3 tools/generate_types.py
```

4. Use the generated types in your code:

**TypeScript**:
```typescript
import { MY_NEW_COMMANDPayload } from './protocol.generated';

const payload: MY_NEW_COMMANDPayload = {
  field1: "hello",
  field2: 42
};
```

**Python**:
```python
from app.protocol_generated import MY_NEW_COMMANDPayload

payload: MY_NEW_COMMANDPayload = {
    "field1": "hello",
    "field2": 42
}
```

### Adding a New Event

Same process as commands, but add to the `"events"` section:

```json
{
  "events": {
    "MY_NEW_EVENT": {
      "payload": {
        "type": "object",
        "required": ["data"],
        "properties": {
          "data": {"type": "string"}
        },
        "additionalProperties": false
      }
    }
  }
}
```

### Adding a New Shared Definition

If you have a complex type used in multiple places, add it to `"definitions"`:

```json
{
  "definitions": {
    "MyComplexType": {
      "type": "object",
      "required": ["id", "name"],
      "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"}
      },
      "additionalProperties": false
    }
  }
}
```

Then reference it with `"$ref": "#/definitions/MyComplexType"`.

## JSON Schema Types

Common type mappings:

| JSON Schema | TypeScript | Python |
|-------------|------------|--------|
| `"type": "string"` | `string` | `str` |
| `"type": "integer"` | `number` | `int` |
| `"type": "boolean"` | `boolean` | `bool` |
| `"type": "array", "items": {...}` | `T[]` | `List[T]` |
| `"enum": ["a", "b"]` | `"a" \| "b"` | `Literal["a", "b"]` |
| `"oneOf": [{"type": "string"}, {"type": "null"}]` | `string \| null` | `str \| None` |
| `"$ref": "#/definitions/Foo"` | `Foo` | `Foo` |

## Validation

The schema can also be used for runtime validation (future work):

- **TypeScript**: Use libraries like `ajv` or `zod` (with adapters)
- **Python**: Use `jsonschema` library

## Workflow Example

Let's say you want to add rotation to token movement:

### Old Way (Error-Prone)
1. Update Python handler ✅
2. Update TypeScript sender ❌ (forgot!)
3. Update protocol.md ❌ (forgot!)
4. Ship to production → Bug!

### New Way (Safe)
1. Update `schemas/protocol.json`:
```json
{
  "commands": {
    "MOVE_TOKEN": {
      "payload": {
        "properties": {
          "token_id": {"type": "string"},
          "x_mm": {"type": "integer"},
          "y_mm": {"type": "integer"},
          "rotation_deg": {"type": "integer"}  // ← Added
        },
        "required": ["token_id", "x_mm", "y_mm", "rotation_deg"]
      }
    }
  }
}
```

2. Run generators:
```bash
pnpm generate-types  # TypeScript
python3 tools/generate_types.py  # Python
```

3. TypeScript compiler immediately errors:
```
Property 'rotation_deg' is missing in type...
```

4. Fix frontend code → Everything works!

## Migration Strategy

The generated types are currently **not yet used** in the main codebase. To migrate:

### Phase 1: Gradual Adoption
- Import generated types alongside existing inline types
- Update new code to use generated types
- No breaking changes

### Phase 2: Full Migration
- Replace all inline types with generated types
- Remove duplicate type definitions
- Update all command/event handlers

### Phase 3: Runtime Validation
- Add JSON Schema validation on API boundaries
- Validate incoming commands against schema
- Validate outgoing events against schema

## Tools

- **Type Generator (TypeScript)**: `tools/generate-types.mjs`
- **Type Generator (Python)**: `tools/generate_types.py`
- **Schema**: `schemas/protocol.json`

## Best Practices

1. **Always regenerate types after editing the schema**
2. **Never commit generated files without regenerating**
3. **Use `additionalProperties: false`** to catch typos
4. **Mark all required fields** explicitly in the schema
5. **Use definitions for shared types** to avoid duplication
6. **Document complex schemas** with `"description"` fields

## Future Enhancements

- [ ] Runtime validation using JSON Schema
- [ ] Auto-generate protocol documentation from schema
- [ ] Pre-commit hook to verify types are up-to-date
- [ ] Schema versioning and migration helpers
- [ ] OpenAPI/Swagger spec generation for REST endpoints
