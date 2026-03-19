# Typed Protocol Schema System

**Status**: ✅ Infrastructure Complete | ⏳ Codebase Migration Pending

## What Was Built

A complete schema-based type generation system that provides a **single source of truth** for the WebSocket protocol.

### Infrastructure (Complete)

1. **Schema Definition** (`schemas/protocol.json`):
   - JSON Schema defining all commands, events, and shared types
   - 11 shared definitions (Player, Token, Board, TurnState, etc.)
   - 9 command types (PING, MOVE_TOKEN, START_GAME, etc.)
   - 17 event types (PONG, HELLO, TOKEN_MOVED, etc.)

2. **TypeScript Generator** (`tools/generate-types.mjs`):
   - Generates type-safe TypeScript interfaces and types
   - Output: `apps/web/src/protocol.generated.ts`
   - Integrated into build process (`prebuild` script)

3. **Python Generator** (`tools/generate_types.py`):
   - Generates type-safe Python TypedDicts and Literals
   - Output: `services/api/app/protocol_generated.py`
   - Passes mypy type checking

4. **Documentation**:
   - `schemas/README.md` - Complete usage guide
   - This document - Implementation summary

## Example: Before vs After

### Before (Manual Type Maintenance)

**TypeScript (apps/web/src/ui/App.tsx)**:
```typescript
// Manually maintained types
type MOVE_TOKENPayload = {
  token_id: string;
  x_mm: number;
  y_mm: number;
};
```

**Python (services/api/app/main.py)**:
```python
# Manually validated
token_id = payload.get("token_id")  # Hope this matches!
x_mm = payload.get("x_mm")
y_mm = payload.get("y_mm")
```

**Problems**:
- Types drift between frontend and backend
- Typos caught only at runtime
- Forgetting fields causes bugs
- Protocol documentation out of sync

### After (Schema-Generated Types)

**Schema (schemas/protocol.json)** - Single Source of Truth:
```json
{
  "commands": {
    "MOVE_TOKEN": {
      "payload": {
        "type": "object",
        "required": ["token_id", "x_mm", "y_mm"],
        "properties": {
          "token_id": {"type": "string"},
          "x_mm": {"type": "integer"},
          "y_mm": {"type": "integer"}
        }
      }
    }
  }
}
```

**TypeScript** - Auto-Generated:
```typescript
import { MOVE_TOKENPayload } from './protocol.generated';

const payload: MOVE_TOKENPayload = {
  token_id: "A",
  x_mm: 300,
  y_mm: 200
  // Compiler error if you forget a field!
};
```

**Python** - Auto-Generated:
```python
from app.protocol_generated import MOVE_TOKENPayload

payload: MOVE_TOKENPayload = {
    "token_id": "A",
    "x_mm": 300,
    "y_mm": 200
    # mypy error if you forget a field!
}
```

**Benefits**:
- ✅ One place to update (the schema)
- ✅ Compilers catch errors before runtime
- ✅ Frontend and backend guaranteed to match
- ✅ Self-documenting protocol

## How to Use

### 1. Generate Types

**TypeScript** (auto-runs before build):
```bash
cd apps/web
pnpm generate-types
```

**Python**:
```bash
python3 tools/generate_types.py
```

### 2. Import Generated Types

**TypeScript**:
```typescript
import {
  CommandType,
  EventType,
  MOVE_TOKENPayload,
  TOKEN_MOVEDPayload,
  Token,
  Player,
  // ... all other types
} from './protocol.generated';
```

**Python**:
```python
from app.protocol_generated import (
    CommandType,
    EventType,
    MOVE_TOKENPayload,
    TOKEN_MOVEDPayload,
    Token,
    Player,
    # ... all other types
)
```

### 3. Use Types in Your Code

Instead of inline types or `unknown`, use the generated types for complete type safety.

## Next Steps: Codebase Migration

The infrastructure is ready, but the codebase still uses inline types. Here's the migration path:

### Phase 1: Non-Breaking Adoption (Low Risk)

**Goal**: Use generated types in new code alongside existing types

**Tasks**:
1. Import generated types in `App.tsx` and `main.py`
2. Use generated payload types for new command handlers
3. Keep existing inline types temporarily
4. No breaking changes

**Estimate**: 1-2 hours

### Phase 2: Replace Inline Types (Medium Risk)

**Goal**: Remove all duplicate type definitions

**Tasks**:
1. **TypeScript (apps/web/src/ui/App.tsx)**:
   - Remove inline type definitions (lines ~8-63)
   - Import from `protocol.generated.ts` instead
   - Update type guards to use generated types

2. **Python (services/api/app/main.py)**:
   - Replace ad-hoc TypedDicts with generated ones
   - Import from `protocol_generated.py`
   - Use generated types in function signatures

**Estimate**: 2-4 hours

**Testing**: All existing tests should pass without modification

### Phase 3: Runtime Validation (Optional, Future)

**Goal**: Validate incoming commands and outgoing events against schema

**Tasks**:
1. Add JSON Schema validation library (Python: `jsonschema`, TypeScript: `ajv`)
2. Validate all incoming commands on the API
3. Validate all outgoing events (dev mode only)
4. Add validation error handling

**Benefits**:
- Catch malformed messages at runtime
- Better error messages for debugging
- Defense against protocol violations

**Estimate**: 4-6 hours

## Migration Example: MOVE_TOKEN

Here's a concrete example of migrating the MOVE_TOKEN handler:

### Before (Current Code)

**TypeScript**:
```typescript
// Inline type
type SomePayload = {
  token_id: string;
  x_mm: number;
  y_mm: number;
};

// Usage
ws.send(JSON.stringify({
  kind: "COMMAND",
  type: "MOVE_TOKEN",
  client_msg_id: "123",
  payload: { token_id: "A", x_mm: 300, y_mm: 200 }
}));
```

**Python**:
```python
# Ad-hoc validation
if command_type == "MOVE_TOKEN":
    token_id = payload.get("token_id")
    x_mm = payload.get("x_mm")
    y_mm = payload.get("y_mm")
```

### After (Using Generated Types)

**TypeScript**:
```typescript
import { MOVE_TOKENPayload, CommandEnvelope } from './protocol.generated';

const payload: MOVE_TOKENPayload = {
  token_id: "A",
  x_mm: 300,
  y_mm: 200
};

const command: CommandEnvelope = {
  kind: "COMMAND",
  type: "MOVE_TOKEN",
  client_msg_id: "123",
  payload
};

ws.send(JSON.stringify(command));
```

**Python**:
```python
from app.protocol_generated import MOVE_TOKENPayload

if command_type == "MOVE_TOKEN":
    # Cast payload to typed dict for type safety
    move_payload: MOVE_TOKENPayload = payload  # type: ignore
    token_id = move_payload["token_id"]
    x_mm = move_payload["x_mm"]
    y_mm = move_payload["y_mm"]
```

## Verification

All infrastructure is tested and working:

- ✅ Schema is valid JSON Schema (draft-07)
- ✅ TypeScript types generate correctly
- ✅ Python types generate correctly
- ✅ TypeScript types compile without errors
- ✅ Python types pass mypy checking
- ✅ Build integration works (`prebuild` script)
- ✅ Documentation complete

## Files Added

```
schemas/
├── README.md              # Usage guide
└── protocol.json          # Schema definition

tools/
├── generate-types.mjs     # TypeScript generator
└── generate_types.py      # Python generator

apps/web/src/
└── protocol.generated.ts  # Generated TypeScript types

services/api/app/
└── protocol_generated.py  # Generated Python types

docs/
└── typed-protocol-schema.md  # This file
```

## Recommendation

**Start with Phase 1**: Begin using generated types for new code while leaving existing code untouched. This provides immediate value with zero risk.

Once comfortable, proceed to Phase 2 to complete the migration and remove all duplicate type definitions.

Phase 3 (runtime validation) is optional but provides additional safety for production use.

## Questions?

See `schemas/README.md` for detailed usage examples and best practices.
