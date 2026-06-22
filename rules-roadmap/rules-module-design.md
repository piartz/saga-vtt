# Rules Module Design

## Goals
- Keep the server authoritative for every rules-relevant decision.
- Keep the VTT core independent from any single ruleset.
- Make rules decisions replayable from commands, events, random rolls, and snapshots.
- Support generic modules first, then a compatible module backed by original code and data.
- Use canonical game names/labels where helpful, but avoid bundling copied rule prose, artwork, battle-board layout, or published explanatory/scenario text.

## Boundary

### VTT Core Owns
- Rooms, player connections, presence, and event sequencing.
- Board coordinate space, token storage, and generic geometry helpers.
- Dice rolling infrastructure and audit metadata.
- Command/event transport and generated protocol types.
- Generic UI rendering and input capture.
- Persistence and replay infrastructure when added.

### Rules Module Owns
- Game phase definitions and legal command windows.
- Warband schema, unit traits, equipment tags, and derived stats.
- SAGA dice generation and spend rules.
- Ability timing, costs, trigger restrictions, and effect composition.
- Activation legality and consequences.
- Fatigue/exhaustion thresholds and spend effects.
- Combat pipelines for shooting and melee.
- Terrain trait interpretation.
- Scenario setup, deployment, objective tracking, and scoring.

### Shared Contract
The core should call a `RulesModule`-style interface that can answer:

- What phases exist and what commands are legal now?
- What derived state should be included in snapshots?
- Can this command be applied to this state?
- What events, random rolls, and state mutations result?
- What UI affordances should the client show for the active player?

The exact interface should wait until the first implementation phase, but every design decision should preserve this separation.

## Domain Model Categories

### Module Metadata
- Module id, display name, version, supported protocol version.
- Feature flags for optional capabilities such as scenario setup, custom abilities, or persistence migrations.

### Game State
- Current phase and active player.
- Scenario state: setup stage, deployment zones, turn limit, objectives, score.
- Player state: SAGA dice pool, pending choices, available reactions.
- Unit state: ownership, type, figure count, equipment tags, fatigue, exhaustion state, activation history, position/formation.
- Terrain state: geometry, type traits, cover/visibility/movement effects.
- Ability state: allocated SAGA dice, prepared abilities, used-once markers, lingering effects.

### Commands
Initial commands should stay coarse and intent-focused:

- Setup: choose scenario, place terrain, deploy unit, confirm setup.
- Orders phase: roll SAGA dice, allocate SAGA dice, trigger Orders ability.
- Activation phase: activate unit, move unit, declare charge, declare shooting, rest unit.
- Reaction windows: spend fatigue, trigger reaction ability, pass reaction.
- Combat choices: select target, close ranks or equivalent defensive choice, choose ability, choose casualties, resolve withdrawal.
- End state: end phase, end turn, concede.

### Events
Events should be facts with enough payload to replay and audit:

- SAGA dice generated, allocated, spent, removed.
- Ability triggered and effects applied.
- Unit activated, moved, charged, shot, rested.
- Fatigue added, removed, spent, exhaustion changed.
- Attack/defense dice rolled with roll reason and target.
- Hits assigned, saves/cancellations applied, casualties removed.
- Terrain placed, deployment completed, score updated.
- Reaction window opened, resolved, or expired.

## Ability Engine Shape
The rules require an ability system with timing windows and costs. Avoid hard-coding every ability into command routing.

Recommended layers:

- **Ability definition**: id, phase/timing keyword, cost expression, restrictions, once-per-turn behavior, effect pipeline.
- **Trigger context**: current event, acting player, unit, target, terrain, pending combat, available SAGA dice.
- **Effect primitives**: add dice, reroll dice, modify target number, add/remove fatigue, cancel hits, move unit, open choice.
- **Resolver**: validates cost/restrictions, consumes SAGA dice, records event, applies effects.

Canonical ability and special-rule names may be stored and displayed. Published ability prose should not be stored; implement the behavior in original code and keep descriptions short, functional, and non-quoted.

## Geometry Needs
The current token movement model is enough for simple tabletop movement but not enough for full rules enforcement. Future geometry helpers should support:

- SAGA range bands as named distances backed by mm/inch conversion:
  - `VS` = 2 inches
  - `S` = 4 inches
  - `M` = 6 inches
  - `L` = 12 inches
  - numeric prefixes multiply the ruler length, e.g. `2L` = 24 inches.
- Unit formation validation across multiple figures.
- Base sizes and model footprint checks.
- Straight-line movement paths and path length limits.
- Contact detection for charges.
- Terrain overlap and terrain-crossing detection.
- Line-of-sight and cover queries.
- Legal casualty removal without breaking formation.

These helpers should remain generic core utilities. The rules module should decide how their results matter.
