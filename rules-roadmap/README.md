# Rules Module Roadmap

This directory plans the rules-module work for the skirmish VTT. It is intentionally documentation-only: no rules implementation, copied rule prose, published examples, battle-board layout, or artwork should be committed here.

The near-term goal is to grow from the current generic tabletop loop into a rules-aware game engine through small, test-backed increments. The VTT core should remain reusable, while rules-specific behavior lives behind explicit module boundaries.

## Source Handling
- Treat local commercial rulebooks as reference material for behavior and terminology.
- Use canonical names/labels for units, terrain, special rules, battle-board abilities, scenarios, and other game terms.
- Encode mechanics as original code, state transitions, tests, and data structures.
- Do not copy explanatory rule prose, published examples, authored ability descriptions, battle-board layout, scenario prose, or artwork.

## Roadmap Files
- [rules-module-design.md](rules-module-design.md): target boundaries and domain model categories.
- [implementation-plan.md](implementation-plan.md): phased implementation rounds.
- [iteration-playbook.md](iteration-playbook.md): how to keep each round small, reviewable, and verifiable.

## High-Level Rules Categories
The rulebook structure maps cleanly into these implementation categories:

- **Game setup**: board dimensions, player sides, terrain placement, deployment, scenario metadata.
- **Warband model**: factions, units, unit types, equipment tags, figure counts, and SAGA dice generation thresholds.
- **Measurement and geometry**: SAGA range bands (`VS`, `S`, `M`, `L`, and numeric multiples such as `2L`), base sizes, formation constraints, line of sight, contact, collision, and impassable areas.
- **Turn engine**: alternating player turns, Orders phase, Activation phase, end-of-turn cleanup.
- **SAGA dice engine**: generated SAGA dice, result symbols, reusable and single-use abilities, ability timing windows.
- **Activations**: move, charge, shoot, rest, free/cancelled activations, repeat activation costs.
- **Fatigue and exhaustion**: fatigue gain/removal, opponent fatigue spend windows, penalties to movement and combat.
- **Combat resolution**: shooting and melee pipelines, attack pools, defense rolls, modifiers, casualty removal, post-combat movement.
- **Terrain**: terrain size/type traits and their effects on movement, cover, visibility, fatigue, and scenario setup.
- **Special rules and equipment**: unit keywords, mounts, ranged weapons, armor modifiers, Bodyguards, and keyword-driven exceptions.
- **Scenario and scoring**: terrain setup rules, deployment, turn count, victory conditions, and score calculation.
- **Audit and replay**: server-side validation, deterministic event stream, dice audit trail, undo/rewind boundaries.
