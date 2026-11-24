# Agent Context

Last updated: 2026-11-24 (confirmed close-ranks equipment correction; documentation only)

Purpose: persistent, fast-loading context for agentic coding tools so each new session can avoid rescanning the whole repo.

## Project Mission
- Build a browser-based, server-authoritative virtual tabletop (VTT) for skirmish play.
- Keep the engine generic and rules-modular, with SAGA mechanics isolated in the rules module.
- Near-term product target: two players can complete a full online game flow with shared state and an audit-friendly action log.

Primary references:
- `docs/vision.md`
- `docs/roadmap.md`
- `docs/architecture.md`

## Constraints (Important)
- Do not commit copyrighted rule prose, published examples, battle-board layout, or artwork.
- Canonical names/labels from the game are allowed in code, tests, and UI for units, terrain, special rules, battle-board abilities, scenarios, and other game terms. Rules behavior may be implemented in original code, but explanatory rulebook prose should not be copied.
- Keep "VTT core" and "rules module" separated.
- Server remains source of truth (moves, dice, legality checks).
- The project owner stated on 2026-11-24 that Studio Tomahawk has authorized the work. Use the local rules as reference for mechanics; retain the repository's original-code/data and no-copied-prose/art boundaries.
- **Do NOT mention AI tools or add "Co-Authored-By" lines in commits or documentation.** Keep all references to development tools and processes neutral.

## Current Implementation Snapshot

### Repo shape
- Monorepo with:
  - `apps/web` (React + TypeScript, Vite)
  - `services/api` (FastAPI + WebSocket)
  - `schemas` (JSON Schema protocol definitions - single source of truth)
  - `tools` (type generators for TypeScript and Python)
  - `docs` (vision, architecture, protocol, roadmap, playbook)
  - `rules-roadmap` (rules-module planning, boundaries, phased implementation plan)
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
  - `.github/workflows/dependabot-auto-merge.yml` enables squash auto-merge for Dependabot PRs whose updates are all patch/minor; majors and minor bumps of `0.x` packages are left for manual review
  - auto-merge waits for the `web`, `api`, and `security` checks, which a repository ruleset on `main` marks as required
- Ruff lint rules are pinned in `services/api/pyproject.toml` (`[tool.ruff.lint] select`) so ruff upgrades cannot widen lint scope; adopting newer rule families is a deliberate, separate change
- A source-based, documentation-only game engine plan now exists under `rules-roadmap/`:
  - `README.md` defines complete playable scope and reading order.
  - `implementation-plan.md` replaces the former Phase 0-10 outline with work packages P00-P15, dependencies, implementation slices, migration obligations, and exit criteria.
  - `rules-coverage.md` maps R01-R34 to the supplied 2022 rulebook, including all core actions, unit/equipment/special rules, setup, terrain, dice, scenarios, and online play requirements.
  - `rules-module-design.md` specifies proposed runtime/state, per-figure geometry, reaction choices, event transactions, protocol evolution, content packs, UI, and recovery.
  - `validation-and-release.md` defines focused tests and full-game/restart/replay acceptance scripts.
  - `decisions-and-source-gaps.md` records engineering defaults, explicit digital adaptations, owner rulings, remaining source questions, and missing complete faction material. Q01-Q04 are resolved: C means S; Resilience exchanges may reach exhaustion but cannot start exhausted and cancel up to X casualties per fatigue; use bands/inches; Presence only affects SAGA abilities. Corrected Q05: close ranks is charge-only, never against shooting; Improvised Projectiles forbids it, superseding the earlier permission. Other prohibited equipment/status includes bows/slings, javelins, crossbows, horse mounts, heavy weapons, and Unarmed; retain composite bows and further sourced restrictions. The list is non-exhaustive.
  - `generic-warband.md` defines the first implementation target: four CORE-2022 base profiles, all inherited troop rules, and seven owner-selected loadouts. Corrected Q06 supersedes earlier owner-supplied numbers: base Armour is 5 for Warlord/Hearthguards and 4 for Warriors/Levies; horses and bows derive Armour penalties. Levy base Aggression is 1/3 melee / 1/2 shooting, with melee 1/2 without ranged weapons; Warrior shooting Aggression is 1/2. Both Warlord loadouts retain Determination, We Obey, Presence, Bodyguards, Pride, and Resilience(1). Q07-Q10 set cancellation before Activation/Reaction, consumption of cancelled free attempts including Old Grudge, unit formation during scenario-directed deployment, and coin tosses for tied initiative d6 rolls.
  - `iteration-playbook.md` gives per-slice implementation and handoff instructions.
  - `review-readiness.md` records the final source/code review. Corrections make intermediate movement/deployment cohesion, sight versus movement gaps, combat fatigue prohibitions, pre-pool limits, preview versus enforced-play capability gates, and transactional dedupe explicit. The legacy onboarding task list now points to the P00-P15 plan.
  - Q11 resolves Clash's quota: first player declares final unit count N including Warlord before deployment; first batch is ceil(N/2) including Warlord, then opponent-all, then floor(N/2). Sizes/equipment remain deployment-time choices; every commitment must leave a feasible remaining partition matching N.
  - The plan was checked against `rules/SAGA_-_Rulebook_2022_261124_161828.pdf`; the PDF is a local untracked reference, not a committed asset. No engine, schema, protocol, or data-model implementation changed with this plan.
- Rules-module scaffolding has started (Phase 0 in the previous roadmap):
  - `services/api/app/rules/` contains a placeholder rules module interface, registry, and passive `saga-core` module metadata
  - `GET /rules/modules` lists registered modules
  - `GET /rules/modules/{module_id}` returns passive module manifests with canonical game terminology for unit types, terrain traits, ability timings, and scenario metadata
  - Unit type manifests expose SAGA dice generation thresholds via `generates_saga_dice_at_figures`
  - `POST /games` accepts optional `rules_module_id` and rejects unknown module ids
  - room creation, active-room listings, and `HELLO` snapshots include `rules_module`
  - room creation and `HELLO` snapshots include passive unit state seeded from SAGA Core (`Unit`)
  - protocol schema and generated TypeScript/Python protocol types include `RulesModule` and `Unit`
- SAGA distance bands for future measurement work:
  - `VS` = 2 inches, `S` = 4 inches, `M` = 6 inches, `L` = 12 inches
  - numeric prefixes multiply the band, e.g. `2L` = 24 inches
  - current documents/runtime use integer mm; the plan proposes versioned fixed-point 0.1 mm internal coordinates preserving exact inch conversions. Per owner instruction, player-facing distances use bands or inches, C normalizes to S in distance contexts, table is 48 x 36 inches, ruler width is 1 inch, and no metric rules mode is planned. This remains unimplemented.
- **Typed Protocol Schema System**:
  - Single source of truth for WebSocket protocol in `schemas/protocol.json`
  - Auto-generates TypeScript types (`apps/web/src/protocol.generated.ts`)
  - Auto-generates Python TypedDicts (`services/api/app/protocol_generated.py`)
  - Schema now matches runtime token and ping/pong payload shape (`label`/`r_mm`, `PING.client_time`, `PONG.echo`)
  - Phase 1 adoption started in runtime code:
    - `apps/web/src/ui/App.tsx` now imports generated envelope/state types
    - `services/api/app/main.py` now imports generated protocol TypedDict/Literal aliases and payload types
  - TypeScript generation runs automatically before build (`prebuild` script)
  - See `schemas/README.md` and `docs/typed-protocol-schema.md` for details
- Bootstrap script `tools/setup-and-run.sh` is interactive and platform-aware:
  - detects Linux/macOS
  - prompts before tool install/upgrade
  - uses installer fallbacks (pnpm prefers Homebrew on macOS)

### Backend (`services/api/app/main.py`, `services/api/app/connections.py`)
- `GET /health` returns status + UTC time.
- `POST /games` creates in-memory room with:
  - random `game_id`
  - `protocol_version = 1`
  - board size `800x500` mm
  - default tokens A/B
  - default passive units `A-warlord` and `B-warlord`, anchored to tokens A/B with no owner assigned yet
- Per-room websocket transport/presence state is isolated in `RoomConnectionManager`:
  - registers/removes websocket connections
  - assigns ephemeral player identities
  - provides player snapshots and connected-player ordering
  - handles broadcast fan-out and stale websocket cleanup
- `WS /games/{game_id}/ws`:
  - accepts connection
  - assigns ephemeral player identity per connection
  - emits `HELLO` event with protocol version, board, token snapshot, unit snapshot, and player list
  - emits `PLAYER_JOINED` to existing clients when a new player connects
  - emits `PLAYER_LEFT` to remaining clients when a player disconnects
  - handles `PING` -> broadcasts `PONG` with echoed payload (`client_time` when provided)
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
- `services/api/tests/test_rules_modules.py`
  - verifies module listing/manifests, room selection, passive unit snapshots, and basic unit validation
  - does not verify SAGA gameplay; its recruitment-sized unit validation needs separation from surviving-unit validation in P02
- `services/api/tests/test_connections.py`
  - verifies `RoomConnectionManager` player assignment and snapshots
  - verifies broadcast exclusion and stale websocket cleanup
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
   - keep core usable with the SAGA Core module first
4. Accounts/persistence:
   - database-backed games/events/snapshots
   - replays and spectators

## Next Recommended Tasks
- Follow `rules-roadmap/README.md` and the P00-P15 plan; the old Phase 0-10 numbering is superseded.
- Start P00.1: establish the source/requirement registry and pin the supplied book revision; apply resolved owner rulings Q01-Q11 and prioritize the generic pack. Specify generic activation/board content for full play; named faction sources are later work.
- Carry the final review's source interpretations and regression cases into that registry, including p.26's pre-pool bonus limit despite the conflicting p.29 example. No further owner rule decision blocks P00/P01.
- Apply corrected Q05 throughout P10/P11: definition-level close-ranks prohibitions include Improvised Projectiles; test every listed restriction, combinations, additional restricting definitions, and an eligible ordinary foot defender.
- Then start P01.1: extract command dispatch and introduce deterministic reduction/event-store contracts while retaining sandbox behavior.
- Continue P01 with stable seats, dedupe/version checks, pause/resume, and an enforced-mode boundary before adding rules-dependent commands.
- Use P02-P03 for source-backed base profiles, inherited rules and derived equipment characteristics, actual ownership, recruitment versus surviving-unit validation, individual figures, and exact geometry. Follow corrected Q06 and the generic-warband tables; passive metadata does not count as completed rules enforcement.
- **Complete remaining Phase 1 adoption and begin Phase 2 cleanup** (remove remaining duplicate inline protocol types/parsers in `apps/web/src/ui/App.tsx` and `services/api/app/main.py`).
- Extract command routing/dispatch out of the websocket loop now that transport/presence state is isolated.
- Add WS reconnect/backoff client wrapper with resync behavior.
- Implement the planned disconnect pause/resume policy in P01/P14; today's runtime still auto-passes the disconnected active player's turn.
- Expand dice UX (custom notation input + richer readable log details/filters for `DICE_ROLLED`).
- Add deployment workflow with explicit manual approval gate for production (CI step 4).
- Start ADRs for major protocol/state decisions in `docs/adrs/`.
- Decide whether to adopt ruff's wider default rules (UP/SIM/B/RUF/I families; about 138 findings, mostly auto-fixable) in a dedicated cleanup PR.
- Add a minimal web smoke test so web dependency updates are checked for runtime breakage, not only lint and build.

## Open Decisions / Risks
- The new plan is documentation only. Today's d20 initiative, 800x500 mm board, token activations, generic dice, and permissive movement remain bootstrap behavior, not source-verified SAGA enforcement.
- The generic warband is the initial target; named faction lists/boards are no longer an initial implementation gate. Generic profiles do not yet specify an activation/board model, which is still needed before a complete generic game can be claimed. Troop values and special rules now come from CORE-2022 pp.44-47 and referenced equipment sections; earlier generic numerical overrides are superseded. Base Armour must remain separate from derived modifiers. Shooting characteristics do not grant ordinary ranged actions to loadouts without a weapon.
- Owner rulings resolve Q01-Q11. Deployment quota/counting is scenario-defined; Clash fixes only the first player's declared total unit count before deployment, not future groupings/equipment. Do not impose that procedure globally. Close ranks is only against charges, never shooting; corrected Q05 forbids it for Improvised Projectiles and the other listed equipment/status categories. Restrictions are extensible; the earlier Improvised Projectiles permission is superseded. Do not reopen these rulings; future source gaps must be tracked separately.
- The final review supports starting P00/P01 against the supplied book and owner rulings. Generic board costs/effects remain a P12 content gate; official FAQ currency is unverified. P03 must prove geometry feasibility/tolerance behavior, and enforced play must remain unavailable while any selected pack/scenario capability is missing. A roster preview is not evidence of playable rules enforcement.
- The plan selects per-figure geometry, fixed-point coordinates, fixed player seats, serialized event transactions, disconnect pause, and durable storage before release. These are proposed defaults, not implemented capabilities; see `rules-roadmap/decisions-and-source-gaps.md`.
- Planned event ordering/replay/reconnect contracts are documented, but runtime support is not implemented.
- No stable seat authentication or unit ownership enforcement: current active-player restrictions alone do not provide the planned authorization model.
- Presence identities are ephemeral per websocket and not stable across reconnect.
- In-memory room state means process restart loses all games.
- Connection/presence transport state is isolated, but the websocket handler still owns command dispatch and disconnect game-state policy.
- Generated protocol types are now partially adopted, but runtime validation still relies on custom parsing/guards; full Phase 2 duplicate-type cleanup is still pending.
- Unit ownership is currently nullable and default units are temporarily anchored to single visual tokens; setup/deployment needs to assign owners before unit state can drive SAGA dice or activation legality.
- Rules-module work may use canonical game names/labels for units, terrain, special rules, battle-board abilities, scenarios, and similar terms. The remaining content boundary is copied prose, published examples, battle-board layout, artwork, and other expressive source material.
- Full rules enforcement will require richer unit geometry than the current single-token movement model, including formation, base footprint, contact, line-of-sight, terrain overlap, and casualty-removal validation.
- Measurement work should use SAGA range labels (`VS`, `S`, `M`, `L`, multiples and ordered sums) and exact imperial conversions; do not perpetuate whole-mm rounding when implementing the planned precision migration.
- Dependabot auto-merge relies on CI as its only safety gate. The web app has no runtime/UI tests, so a web dependency regression that still lints and builds would merge unnoticed.
- Auto-merges are performed with `GITHUB_TOKEN`, which does not trigger the `push` CI run on `main`; the PR's CI run is the only check for those commits.
- The `security` CI job is advisory: audit and bandit findings emit warnings and never fail the job.
- Dependabot vulnerability alerts and security updates are intentionally disabled until the app reaches MVP; only scheduled version updates are active.

## Quick Session Bootstrap (for agents)
1. Read this file.
2. Read `docs/llm-playbook.md`.
3. Open:
   - `services/api/app/main.py`
   - `apps/web/src/ui/App.tsx`
   - `apps/web/src/ui/Board.tsx`
4. For engine work, read `rules-roadmap/README.md` and select the next prerequisite-complete Pxx slice; use `docs/roadmap.md` for broader product work.
5. If behavior changes, update this file before ending the session.
