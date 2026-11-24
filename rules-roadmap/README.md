# SAGA Game Engine Plan

Planning baseline: **2026-11-24**, repository commit `f1cd5c6`. This directory specifies the work to take the existing shared tabletop through a complete, server-enforced, two-player SAGA game. This change is documentation only; none of the proposed behavior is implemented by this plan.

The project owner has stated that Studio Tomahawk has authorized the work. Use the supplied local rulebook to implement mechanics in original code and data. Keep rules-specific content outside the VTT core and keep copied prose, published examples, battle-board layouts, and artwork out of documents, tests, and code. The local PDF remains untracked.

## Read in this order

1. [Project context](../docs/agent-context.md): what actually exists today.
2. [Implementation plan](implementation-plan.md): scope, dependencies, work packages, and exit criteria.
3. [Rules coverage](rules-coverage.md): source locations, required mechanics, and acceptance cases by stable requirement ID.
4. [Module design](rules-module-design.md): proposed state, transactions, timing, geometry, protocol evolution, and UI responsibilities.
5. [Validation and release](validation-and-release.md): test strategy and complete-game acceptance scripts.
6. [Decisions and source gaps](decisions-and-source-gaps.md): engineering defaults, rule questions, and missing content.
7. [Iteration playbook](iteration-playbook.md): instructions for executing one implementation slice.

These files replace the earlier Phase 0-10 outline. Use work-package IDs `P00`-`P15` and requirement IDs `R01`-`R34`; new package numbers do not correspond to old phases. The passive module and unit metadata are scaffolding, not completed rules enforcement.

## What playable means

Two players can select supported factions and legal warbands, set up Clash of Warlords, deploy individual figures, roll and allocate SAGA dice, use the complete selected battle boards, move, manoeuvre, charge, shoot, rest, spend fatigue, resolve reactions and casualties, finish the scenario, and see an explainable result. Either player can reconnect during a pending choice without changing the game. A saved game can resume after a server restart. No console commands or manual state edits are required.

The first release covers all core mechanics and options in the supplied 2022 book, including all three deployment methods, seven terrain presets, six optional battlefield-chaos results, equipment, and core special rules. It also requires at least two complete faction packs. The core PDF does **not** contain complete faction lists and battle boards; their acquisition and verification are a release dependency. Fixture-only play does not meet the release definition.

Additional Universes, named Heroes, mercenary/Legendary profiles, creatures, magic, buildings beyond the core ruins treatment, other scenarios, campaigns, and multiplayer require their own sources and follow-on packs. Their extension points and core restrictions are included here. They are not implicitly included in the first release.

## Immediate next slice

Start with `P00.1`: establish the versioned source baseline and decision register. Then take `P01.1`: extract command dispatch and deterministic state reduction while retaining the bootstrap behavior. Neither task requires guessing faction content.
