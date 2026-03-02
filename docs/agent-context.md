# Agent Context

Last updated: 2026-03-03

Purpose: persistent, fast-loading context for agentic coding tools so each new session can avoid rescanning the whole repo.

## Project Mission
- Build a browser-based, server-authoritative virtual tabletop (VTT) for skirmish play.
- Keep the engine generic and rules-modular (Saga-ready, not Saga-IP bundled).
- Near-term product target: two players can complete a full online game flow with shared state and an audit-friendly action log.

Primary references:
- `docs/vision.md`
- `docs/roadmap.md`
- `docs/architecture.md`

## Constraints (Important)
- Do not commit copyrighted rule text, unit profiles, battle boards, or artwork.
- Keep "VTT core" and "rules module" separated.
- Server remains source of truth (moves, dice, legality checks).

## Current Implementation Snapshot

### Repo shape
- Monorepo with:
  - `apps/web` (React + TypeScript, Vite)
  - `services/api` (FastAPI + WebSocket)
  - `docs` (vision, architecture, protocol, roadmap, playbook)
- Bootstrap script `tools/setup-and-run.sh` is interactive and platform-aware:
  - detects Linux/macOS
  - prompts before tool install/upgrade
  - uses installer fallbacks (pnpm prefers Homebrew on macOS)

### Backend (`services/api/app/main.py`)
- `GET /health` returns status + UTC time.
- `POST /games` creates in-memory room with:
  - random `game_id`
  - `protocol_version = 1`
  - board size `800x500` mm
  - default tokens A/B
- `WS /games/{game_id}/ws`:
  - accepts connection
  - emits `HELLO` event with protocol version, board, token snapshot
  - handles `PING` -> broadcasts `PONG`
  - handles `MOVE_TOKEN`:
    - validates payload shape/types
    - validates integer mm coordinates
    - validates board bounds using token radius
    - mutates room token state
    - broadcasts `TOKEN_MOVED` with updated token + `client_msg_id`
  - handles `ROLL_DICE`:
    - validates payload shape/types (`count`, `sides`, optional `modifier`)
    - enforces bounds (`count: 1..20`, `sides: 2..1000`, `modifier: -1000..1000`)
    - rolls server-side via `secrets`
    - broadcasts `DICE_ROLLED` with `rolls`, `total`, `notation`, and `client_msg_id`
  - emits `ERROR` events for bad input/unknown commands
  - cleans up room when last connection leaves

### Frontend (`apps/web/src/ui`)
- Opens WS connection for current room.
- Displays connection status and event log.
- Supports:
  - create room (`POST /games`)
  - set room id manually
  - send `PING`
  - send sample `ROLL_DICE` (`3d6+1`)
  - board token drag and release -> sends `MOVE_TOKEN`
- Applies authoritative updates from events:
  - `HELLO` token snapshot
  - `TOKEN_MOVED` token updates
- Board UI:
  - SVG board with mm coordinate system
  - local drag preview
  - sends command on release (server confirms via event)

### Tests
- `services/api/tests/test_health.py`
- `services/api/tests/test_rooms_and_moves.py`
  - verifies room creation
  - verifies authoritative token move broadcast to two WS clients
  - verifies authoritative dice roll broadcast to two WS clients
  - verifies dice payload validation errors

## Docs vs Code Notes
- Docs often describe "starter/placeholder" behavior.
- Current code already includes token movement command/event path and room creation endpoint.
- When planning new work, treat implementation state above as canonical unless code changes.

## Future Goals (From Roadmap)
1. Shared tabletop polish:
   - pan/zoom
   - better token placement/selection ergonomics
   - move preview + explicit confirm UX refinement
2. Basic scenario loop:
   - turn structure and active player
   - activation markers
   - server-side dice roller
   - richer action log UI
3. Rules-module interface:
   - explicit `RulesModule` boundary
   - keep core usable with toy ruleset first
4. Accounts/persistence:
   - database-backed games/events/snapshots
   - replays and spectators

## Recommended Next Tasks
- Add typed command/event schemas on server and client (single source of truth).
- Introduce per-room connection manager abstraction (easier JOIN/LEAVE/presence).
- Add WS reconnect/backoff client wrapper with resync behavior.
- Expand dice UX (custom notation input + structured action log rendering for `DICE_ROLLED`).
- Start ADRs for major protocol/state decisions in `docs/adrs/`.

## Open Decisions / Risks
- Event ordering and replay consistency under reconnect are not yet specified.
- No auth/identity: all clients can currently issue movement and dice commands.
- In-memory room state means process restart loses all games.
- Protocol evolution strategy is documented but not yet exercised in code.

## Quick Session Bootstrap (for agents)
1. Read this file.
2. Read `docs/llm-playbook.md`.
3. Open:
   - `services/api/app/main.py`
   - `apps/web/src/ui/App.tsx`
   - `apps/web/src/ui/Board.tsx`
4. Check `docs/roadmap.md` and pick a smallest useful increment.
5. If behavior changes, update this file before ending the session.
