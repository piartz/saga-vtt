# Architecture

## Core idea
The system is **server-authoritative**:
- Clients send **commands** (intent).
- The server validates, applies, and broadcasts **events** (facts).
- The UI replays events to render the same state for both players.

This prevents most cheating and makes replays trivial.

## Components
1. **Web client** (`apps/web`)
   - Renders the board (2D top-down)
   - Provides interaction tools (select, measure, move, rotate)
   - Maintains a local projection of server state via events

2. **API / game server** (`services/api`)
   - Hosts lobby + rooms
   - Owns the source of truth for game state
   - Performs dice rolls and geometry validation
   - Emits an append-only event log

3. **Persistence (later)**
   - PostgreSQL for accounts, games, event logs, snapshots
   - Redis for pub/sub + presence (optional at small scale)

## Suggested data flow
Client:
- connects to `ws://.../games/{game_id}/ws`
- sends: `COMMAND {type, payload, client_msg_id}`
Server:
- replies: `EVENT {type, payload, server_time, seq}`

## Why event-sourcing?
- Replays for free
- Debugging is easier (you can inspect the exact action stream)
- Allows safe evolution with snapshots

## Rules modules
Keep “VTT core” separate from “rules”:
- **VTT core**: tokens, measurement, collisions, dice rolling, turn timer, chat
- **Rules module**: phases, valid actions per phase, combat resolution, scoring

This separation reduces IP risk and keeps the engine usable for other systems.

See `docs/protocol.md` and `docs/data-model.md`.
