# Agent Context

Last updated: 2026-03-19 (typed protocol schema added)

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
- **Do NOT mention AI tools or add "Co-Authored-By" lines in commits or documentation.** Keep all references to development tools and processes neutral.

## Current Implementation Snapshot

### Repo shape
- Monorepo with:
  - `apps/web` (React + TypeScript, Vite)
  - `services/api` (FastAPI + WebSocket)
  - `schemas` (JSON Schema protocol definitions - single source of truth)
  - `tools` (type generators for TypeScript and Python)
  - `docs` (vision, architecture, protocol, roadmap, playbook)
- GitHub Actions CI currently runs:
  - web lint + build (with automatic type generation)
  - API `ruff`, `mypy`, and `pytest` (including integration smoke test)
  - deterministic dependency installs (`pnpm --frozen-lockfile`, `poetry install --sync`)
  - security scanning:
    - `pip-audit` for Python dependency vulnerabilities
    - `bandit` for Python security issues (static analysis)
    - `pnpm audit` for JavaScript dependency vulnerabilities
- Dependabot configured for automatic dependency updates:
  - Python dependencies (weekly, Monday)
  - JavaScript dependencies (weekly, Monday)
  - GitHub Actions (weekly, Monday)
- **Typed Protocol Schema System**:
  - Single source of truth for WebSocket protocol in `schemas/protocol.json`
  - Auto-generates TypeScript types (`apps/web/src/protocol.generated.ts`)
  - Auto-generates Python TypedDicts (`services/api/app/protocol_generated.py`)
  - TypeScript generation runs automatically before build (`prebuild` script)
  - See `schemas/README.md` and `docs/typed-protocol-schema.md` for details
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
  - assigns ephemeral player identity per connection
  - emits `HELLO` event with protocol version, board, token snapshot, and player list
  - emits `PLAYER_JOINED` to existing clients when a new player connects
  - emits `PLAYER_LEFT` to remaining clients when a player disconnects
  - handles `PING` -> broadcasts `PONG`
  - includes `actor_player_id` on player-attributed events (presence, movement, dice, and command errors)
  - includes `self_player_id` in `HELLO.payload` for client-local identity
  - includes turn snapshot in `HELLO.payload.turn` (`phase`, `round`, `active_player_id`)
  - includes initiative snapshot in `HELLO.payload.initiative` (or `null`)
  - handles `START_GAME` -> `INITIATIVE_ROLLED` (d20 roll-off, tie reroll, two-player flow)
  - handles `CHOOSE_TURN_ORDER` (winner chooses `FIRST`/`SECOND`) -> `TURN_ORDER_CHOSEN` then `GAME_STARTED`
  - handles `END_TURN` -> `TURN_CHANGED` turn progression
  - emits `INITIATIVE_RESET` in lobby when initiative becomes invalid due to player join/leave
  - includes undo snapshot in `HELLO.payload.undo` and turn transition events
  - while game is running, enforces active-player-only `MOVE_TOKEN`, `ACTIVATE_TOKEN`, and `ROLL_DICE`
  - handles `MOVE_TOKEN`:
    - validates payload shape/types
    - validates integer mm coordinates
    - validates board bounds using token radius
    - mutates room token state
    - broadcasts `TOKEN_MOVED` with updated token + `client_msg_id`
  - handles `ACTIVATE_TOKEN`:
    - validates payload shape/types (`token_id`, `activation_type`)
    - supports activation types: `move`, `charge`, `shoot`, `rest`
    - token cannot be deactivated manually in-turn; repeated activations are allowed and counted
    - `rest` activation is only valid before any prior activation in the same turn
    - broadcasts `TOKEN_ACTIVATED` with updated token + `client_msg_id`
  - handles `REQUEST_UNDO` for latest board action this turn (`MOVE_TOKEN`/`ACTIVATE_TOKEN`)
    - requires active player and exactly one connected opponent
    - enforces one undo request per player turn
    - emits `UNDO_REQUESTED`
  - handles `RESPOND_UNDO_REQUEST` from opponent (`accept: boolean`)
    - emits `UNDO_APPLIED` with reverted token state when accepted
    - emits `UNDO_REJECTED` when declined
    - emits `UNDO_CANCELLED` if pending request is invalidated by disconnect
  - on `END_TURN`, server clears all token activations and includes token snapshot in `TURN_CHANGED.payload.tokens`
  - handles `ROLL_DICE`:
    - validates payload shape/types (`count`, `sides`, optional `modifier`)
    - enforces bounds (`count: 1..20`, `sides: 2..1000`, `modifier: -1000..1000`)
    - rolls server-side via `secrets`
    - broadcasts `DICE_ROLLED` with `rolls`, `total`, `notation`, and `client_msg_id`
  - emits `ERROR` events for bad input/unknown commands
  - cleans up room when last connection leaves

### Frontend (`apps/web/src/ui`)
- Opens WS connection for current room.
- Displays connection status, connected players, and event log.
- Event log shows actor attribution using `actor_player_id` plus presence labels.
- Event log defaults to human-readable summaries with an "Advanced (JSON)" tab for raw payload inspection.
- Supports:
  - create room (`POST /games`)
  - set room id manually
  - send `PING`
  - send sample `ROLL_DICE` (`3d6+1`)
  - roll initiative (`START_GAME`) and choose turn order (`CHOOSE_TURN_ORDER`)
  - loser waiting prompt: "Waiting for your opponent to choose..."
  - final assignment prompt: "You are the first player" / "You are the second player"
  - start game and end turn commands
  - activate token from hover actions (`ACTIVATE_TOKEN`)
  - request undo for latest board action and respond to opponent undo requests
  - toggle movement confirmation mode
  - board token drag preview with:
    - immediate send on release (confirmation off)
    - one-token-at-a-time pending move + explicit confirm/cancel (confirmation on)
- Applies authoritative updates from events:
  - `HELLO` token + player snapshot
  - `HELLO` self identity + initiative snapshot
  - `INITIATIVE_ROLLED` / `TURN_ORDER_CHOSEN` / `INITIATIVE_RESET` initiative flow updates
  - `HELLO` / `GAME_STARTED` / `TURN_CHANGED` turn snapshot
  - `PLAYER_JOINED` / `PLAYER_LEFT` player presence updates
  - `TOKEN_MOVED` token updates
  - `TOKEN_ACTIVATED` token activation updates
  - `UNDO_REQUESTED` / `UNDO_APPLIED` / `UNDO_REJECTED` / `UNDO_CANCELLED` undo flow updates
  - `TURN_CHANGED.payload.tokens` token activation resets
- Board UI:
  - SVG board with mm coordinate system
  - local drag preview
  - optional one-token-at-a-time move confirmation workflow to avoid chaotic multi-token pending states
  - mouse-wheel zoom (`50%` to `250%`) with +/- controls and reset
  - drag-background panning when zoomed in
  - touchpad two-finger scroll no longer auto-zooms below 100%; panning remains active only when zoomed in
  - Option/Alt or pinch/Cmd/Ctrl wheel gestures trigger board zoom
  - wheel gestures over the board are isolated from page scroll (page scroll continues normally outside board area)

### Tests
- `services/api/tests/test_health.py`
- `services/api/tests/test_rooms_and_moves.py`
  - verifies room creation
  - verifies presence join/leave events and `HELLO` player snapshot
  - verifies authoritative token move broadcast to two WS clients
  - verifies authoritative token activation broadcast to two WS clients
  - verifies rest-activation constraint (rest only before first activation this turn)
  - verifies authoritative dice roll broadcast to two WS clients
  - verifies dice payload validation errors
  - verifies game start, turn progression, and active-player command restrictions
  - verifies only initiative winner can choose turn order
  - verifies move undo requires opponent acceptance and one-undo-per-turn limit
  - verifies activation undo rejection leaves board state unchanged
  - verifies non-board actions cannot be undone
- `services/api/tests/test_integration_smoke.py`
  - comprehensive integration smoke test that validates complete game flow
  - tests room creation, player connection, initiative roll, turn order choice, token movement, token activation, turn progression, and round advancement
  - serves as CI smoke test for end-to-end system validation
- Web UI currently has no automated test suite; board interaction changes are validated via `pnpm build:web` plus manual verification.

## Docs vs Code Notes
- Docs often describe "starter/placeholder" behavior.
- Current code already includes token movement command/event path and room creation endpoint.
- When planning new work, treat implementation state above as canonical unless code changes.

## Future Goals (From Roadmap)
1. Shared tabletop polish:
   - pan/zoom polish (basic controls implemented)
   - better token placement/selection ergonomics
   - move preview + explicit confirm UX refinement (basic one-token confirm flow implemented)
2. Basic scenario loop:
   - activation markers (implemented: repeatable typed activations with per-turn count/last-type tracking)
   - richer action log UI
3. Rules-module interface:
   - explicit `RulesModule` boundary
   - keep core usable with toy ruleset first
4. Accounts/persistence:
   - database-backed games/events/snapshots
   - replays and spectators

## Recommended Next Tasks
- **Migrate codebase to use generated protocol types** (infrastructure complete, see `docs/typed-protocol-schema.md` for migration guide).
- Extract a per-room connection manager abstraction (presence now works but is still inline in `main.py`).
- Add WS reconnect/backoff client wrapper with resync behavior.
- Decide and implement disconnect behavior for turn ownership (pause, auto-pass, or forfeit).
- Expand dice UX (custom notation input + richer readable log details/filters for `DICE_ROLLED`).
- Add deployment workflow with explicit manual approval gate for production (CI step 4).
- Start ADRs for major protocol/state decisions in `docs/adrs/`.

## Open Decisions / Risks
- Event ordering and replay consistency under reconnect are not yet specified.
- No auth/identity: all clients can currently issue movement and dice commands.
- Presence identities are ephemeral per websocket and not stable across reconnect.
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
