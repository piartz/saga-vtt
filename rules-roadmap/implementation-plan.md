# Implementation Plan

This plan is intentionally iterative. Each phase should land as one or more small PRs with focused tests and a short docs update.

## Phase 0: Guardrails and Test Harness

Outcome: a safe place to build rules without copying protected prose or artwork.

- Add a placeholder `RulesModule` interface and a passive SAGA Core module with canonical names. (started)
- Add fixtures for unit types, terrain traits, ability timings, and scenario setup using canonical names where useful. (started)
- Add server tests proving the core can load a module and reject unknown module ids. (started)
- Add documentation for content boundaries and local-only reference material.

Exit criteria:

- No copied rulebook prose, published examples, battle-board layout, or artwork is committed.
- The SAGA Core module can be selected by a room.
- Current generic game flow still works.

## Phase 1: Warband and Unit Model

Outcome: the server understands multi-figure units and derived unit traits.

- Add unit entities separate from visual tokens.
- Represent figure count, unit type, equipment tags, fatigue, and activation history.
- Keep visual token rendering compatible with unit-level state.
- Add basic warband validation for SAGA Core data.
- Add snapshot shape for units and module metadata.

Exit criteria:

- A game can start with module-provided units.
- Unit updates are emitted as authoritative events.
- Tests cover invalid unit definitions and invalid ownership.

## Phase 2: Measurement and Formation Core

Outcome: movement can be validated in rule-relevant terms.

- Add SAGA range bands (`VS`, `S`, `M`, `L`, and numeric multiples such as `2L`) in the rules layer and mm conversion in the core.
- Add base-size and footprint metadata.
- Add formation validation for a unit represented by multiple figures or a simplified formation footprint.
- Add straight-line movement validation and terrain/collision query hooks.

Exit criteria:

- The server rejects out-of-range or formation-breaking movement.
- The UI can display rule-distance labels without owning legality.
- Geometry tests cover edge cases around contact, overlap, and board bounds.

## Phase 3: Turn and Orders Phase

Outcome: the server can run an Orders phase before activations.

- Model the round/turn/phase state machine.
- Generate SAGA dice from surviving units using module rules.
- Add events for SAGA dice generation, allocation, spend, and cleanup.
- Add once-per-turn and reusable SAGA dice slot behavior for SAGA Core abilities.
- Add pending reaction windows for the non-active player.

Exit criteria:

- Players cannot activate units before completing the Orders phase.
- SAGA dice state round-trips through `HELLO` snapshots.
- Tests cover turn changes, SAGA dice caps, unused SAGA dice, and invalid spends.

## Phase 4: Activation Actions

Outcome: units can perform the four primary activation families through module validation.

- Replace the current ad hoc activation types with module-defined activation actions.
- Implement move, charge declaration, shooting declaration, and rest for the SAGA Core module.
- Track repeat activations and fatigue consequences through module rules.
- Emit consistent activation start/resolved/cancelled events.

Exit criteria:

- Illegal activation windows are rejected server-side.
- Repeated activations update fatigue/activation history.
- Undo policy is revisited for multi-step activations.

## Phase 5: Fatigue and Reaction Windows

Outcome: fatigue becomes first-class rules state.

- Add fatigue thresholds and exhaustion state from module rules.
- Add opponent spend windows for movement, shooting, and melee contexts.
- Add pass/trigger reaction commands with timeout-safe defaults.
- Make fatigue spending produce auditable events.

Exit criteria:

- Fatigue can alter movement/combat only through server-approved windows.
- Concurrent clients see the same pending-reaction state.
- Tests cover spend limits, exhaustion, pass behavior, and disconnect behavior.

## Phase 6: Shooting Pipeline

Outcome: ranged combat is resolved as a deterministic server pipeline.

- Add target declaration, range/visibility checks, and eligible attacker count.
- Compute attack dice, modifiers, defense dice, and casualty choices using SAGA Core data.
- Add structured dice events with reason, source unit, target unit, and result summary.
- Add casualty-removal command or deterministic casualty policy for early versions.

Exit criteria:

- Shooting can be replayed from events.
- The UI shows pending choices without computing final legality.
- Tests cover no-line-of-sight, cover, modifiers, saves, and casualty validation.

## Phase 7: Melee and Charge Pipeline

Outcome: charges create contact and immediately resolve melee through a multi-step pipeline.

- Add charge target declaration and legal contact placement.
- Open pre-melee and melee ability/fatigue windows.
- Compute attack and defense pools, roll, apply modifiers, remove casualties, apply fatigue, and resolve withdrawal.
- Decide whether early UI uses simplified unit footprints or individual figure placement.

Exit criteria:

- A melee between two units resolves through events with no client-side authority.
- Multi-step combat can survive reconnect via snapshot state.
- Tests cover invalid multi-target charges, contact rules, casualties, fatigue, and withdrawal.

## Phase 8: Terrain and Scenario Setup

Outcome: scenario setup and terrain traits affect rules.

- Model terrain pieces with size, movement, cover, visibility, and danger traits.
- Add scenario setup stages: choose side, place terrain, deploy units, start game.
- Add scenario objective and score state for a SAGA Core scenario.
- Keep published scenario text out of the repo.

Exit criteria:

- Terrain placement is validated by the server.
- Movement and combat consult terrain traits.
- Score updates are event-driven and replayable.

## Phase 9: Special Rules and Equipment Tags

Outcome: common exceptions are data-driven.

- Add keyword/tag-based rule modifiers for mounts, ranged weapons, armor changes, Bodyguards, and Warlord status.
- Build effect primitives instead of bespoke branches where possible.
- Add compatibility tests showing multiple tags compose predictably.

Exit criteria:

- New tags can be added without changing transport protocol.
- Conflicting effects produce deterministic ordering.
- Tests cover tag composition and unsupported combinations.

## Phase 10: Compatible Module Content Strategy

Outcome: decide how detailed rules content is supplied without bundling protected prose or artwork.

- Decide whether the project will support local user-provided data packs, licensed content, or only built-in implementations that use canonical names and original code.
- Define import validation for external data packs.
- Add clear runtime errors when required external content is missing.
- Keep all committed explanatory text original.

Exit criteria:

- Content boundary is documented.
- The app can distinguish engine support from unavailable proprietary content.
- No copied protected source material is committed.
