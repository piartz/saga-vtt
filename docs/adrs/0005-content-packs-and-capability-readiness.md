# ADR 0005: Declarative content packs and capability readiness

## Status
Accepted (2026-11-24). Records decisions D10 and D13. Pack format first used in P02.1; capability gating enforced at game start from P07, completed in P12. Requirements: R03, R24, R29, R33.

## Context
The plan starts with a generic warband pack and adds sourced faction packs later. Content must be versioned and pinned for replay, kept out of the generic core, and free of copied rules prose or art. A roster that can be previewed is not proof that its rules are playable: a Warlord must not fight with missing Resilience, and an unimplemented ability must not consume dice. The plan left the pack location open ("`services/api/app/rules/packs/` or a dedicated data directory").

## Decision
- **Location and layout.** Packs live in `services/api/app/rules/packs/<pack-id>/<version>/`. Each version directory holds a `pack.json` manifest plus definition files (e.g. profiles, loadouts, equipment, abilities). The generic warband is the first pack.
- **Format and validation.** Definitions are JSON, validated by strict pydantic models with unknown fields rejected. This is the same pattern as the provenance registry in `services/api/app/rules/provenance/`, and needs no new dependency. Validation runs on load and in tests, and checks:
  - references between definitions;
  - numeric limits;
  - version compatibility;
  - source provenance: every definition cites a registry source ID and pages.

  Unknown effects, missing references, recursive cycles, and incompatible versions fail configuration, never mid-game.
- **No executable content.** Ability effects reference reviewed effect handlers registered in code by handler ID. Imported packs are never evaluated as Python or JavaScript.
- **Content boundary.** Packs contain canonical names and labels, numbers, IDs, and source references. They contain no copied rules prose, published examples, battle-board layout, or artwork.
- **Versioning and pinning.** A pack version is `draft` or `released`. A released version is immutable. Its content hash (SHA-256 of a canonical JSON serialization) is locked and checked in tests, so any change needs a new version. Game configuration pins the pack ID, version, and hash; old released versions are kept, or explicitly migrated, so saved games replay unchanged.
- **Capabilities and readiness.** The rules module declares capabilities, e.g. activation grants, ordinary movement, shooting, close ranks, or a named special rule. Each has a support status:
  - `missing`: not implemented;
  - `preview`: its definitions validate and can be inspected, but its behavior is not enforced;
  - `enforced`: its behavior is implemented, with linked requirements and passing tests.

  Packs and scenarios declare the capabilities they need. Configuration produces two separate results: *preview-ready* (definitions valid, nothing `missing` that the roster needs to display) and *enforced-ready* (every required capability `enforced`, and no open registry content gate blocking the pack). An enforced game cannot start unless it is enforced-ready, and the response names what is missing. Test-only fixture abilities are never selectable.

## Consequences
- The generic roster can be previewed in P02 long before it is playable, without overstating support.
- The module manifest gains source/version, capability, and readiness fields (see `rules-roadmap/rules-module-design.md`). That is an API change, made in the first slice that exposes a real capability.
- Effect handlers must be written and reviewed in code before data can use them; content authors cannot add arbitrary behavior.
- Keeping released versions and locked hashes grows the repository slowly, but makes replay and pack drift detectable.
- The existing passive `saga-core` manifest metadata is provisional and is treated as `preview` at most until migrated.
