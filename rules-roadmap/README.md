# SAGA Game Engine Plan

Planning baseline: **2026-11-24**, repository commit `f1cd5c6`. This directory specifies the work to take the existing shared tabletop through a complete, server-enforced, two-player SAGA game. This change is documentation only; none of the proposed behavior is implemented by this plan.

The project owner has stated that Studio Tomahawk has authorized the work. Use the supplied local rulebook to implement mechanics in original code and data. Keep rules-specific content outside the VTT core and keep copied prose, published examples, battle-board layouts, and artwork out of documents, tests, and code. The local PDF remains untracked.

## Read in this order

1. [Project context](../docs/agent-context.md): what actually exists today.
2. [Implementation plan](implementation-plan.md): scope, dependencies, work packages, and exit criteria.
3. [Initial generic warband](generic-warband.md): source-backed profiles, inherited rules, chosen loadouts, deployment, cancellation, and tie-break.
4. [Rules coverage](rules-coverage.md): source locations, required mechanics, and acceptance cases by stable requirement ID.
5. [Module design](rules-module-design.md): proposed state, transactions, timing, geometry, protocol evolution, and UI responsibilities.
6. [Validation and release](validation-and-release.md): test strategy and complete-game acceptance scripts.
7. [Decisions and source gaps](decisions-and-source-gaps.md): engineering defaults, rule questions, and missing content.
8. [Iteration playbook](iteration-playbook.md): instructions for executing one implementation slice.

These files replace the earlier Phase 0-10 outline. Use work-package IDs `P00`-`P15` and requirement IDs `R01`-`R34`; new package numbers do not correspond to old phases. The passive module and unit metadata are scaffolding, not completed rules enforcement.

The [final planning review](review-readiness.md) records the source/code checks, corrections, remaining gates, and recommended starting slice.

## Confirmed rule clarifications

The owner rulings of 2026-11-24 are recorded in the decision register and take precedence over ambiguous source wording: distance C means S; Resilience(X) can exchange up to X casualties for one fatigue while below exhaustion, including the exchange that reaches exhaustion; distances use bands/inches; Presence affects only SAGA abilities; close ranks is available only against a charge, never shooting. Apply these rulings throughout future implementation and tests. Improvised Projectiles permits closing ranks when charged unless another restriction applies (Q05). Q01-Q11 are recorded. Begin with the generic warband; form units during scenario-directed deployment; cancellation consumes paid/free grants before reaction eligibility; use a coin toss for initiative ties. Clash's first player declares the final unit count before deployment, while choosing sizes/equipment during each step (Q11).

The owner's latest correction to Q06 replaces the earlier numerical profiles with CORE-2022 pp.44-47 and the referenced special rules. Keep base Armour separate from derived equipment effects; include every troop rule, including the Levy melee exception without ranged weapons. The chosen seven starter loadouts remain the same.

## What playable means

Two players can select the generic pack and legal warbands (later, supported faction packs), set up Clash of Warlords, deploy individual figures, roll and allocate SAGA dice, use the complete selected battle boards, move, manoeuvre, charge, shoot, rest, spend fatigue, resolve reactions and casualties, finish the scenario, and see an explainable result. Either player can reconnect during a pending choice without changing the game. A saved game can resume after a server restart. No console commands or manual state edits are required.

The first release covers all core mechanics and options in the supplied 2022 book, including all three deployment methods, seven terrain presets, six optional battlefield-chaos results, equipment, and core special rules. Start with the generic pack's owner-selected loadouts and source-backed profiles. A complete generic game still requires an explicitly specified shared battle board/activation economy; profiles alone do not fill that gap. Named faction packs and their complete sources are a later extension, not a prerequisite for starting implementation. Test-only abilities do not count as approved generic gameplay content.

Additional Universes, named Heroes, mercenary/Legendary profiles, creatures, magic, buildings beyond the core ruins treatment, other scenarios, campaigns, and multiplayer require their own sources and follow-on packs. Their extension points and core restrictions are included here. They are not implicitly included in the first release.

## Immediate next slice

Start with `P00.1`: establish the versioned source baseline and decision register. Then take `P01.1`: extract command dispatch and deterministic state reduction while retaining the bootstrap behavior. Neither task requires guessing faction content.
