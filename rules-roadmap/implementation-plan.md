# Game Engine Implementation Plan

**Status:** planning only, 2026-11-24. Baseline: `f1cd5c6`. This replaces the older Phase 0-10 outline. Work packages are not single large pull requests: implement the numbered slices in each package independently and apply the [iteration playbook](iteration-playbook.md).

## Scope and completion

Deliver a server-authoritative, two-player game from room creation to an immutable result, implementing core mechanics with the generic warband's owner-selected loadouts and source-backed profiles first, followed by sourced faction packs. Include recruitment, base/figure geometry, all core terrain and deployment options, Orders/SAGA dice, complete supported battle boards, four activations, manoeuvres, fatigue, shooting/melee/withdrawal, equipment/Hero rules, optional battlefield chaos, scoring, reconnect, save/resume, and usable UI. [R01-R34](rules-coverage.md) are the coverage checklist.

Begin with [the generic warband](generic-warband.md); no named faction sources are required to implement its profiles or core engine. Complete generic play additionally needs an explicitly specified shared board/activation economy; do not silently invent costs or unlimited free actions. Faction sources are required only for later selectable faction content. Additional books/content are separate packs with their own acceptance lists. No undocumented rules shortcuts, manual state edits, or client-authoritative calculations are permitted in the completed game.

## Baseline audit and migration obligations

| Current evidence | Reuse | Required change |
| --- | --- | --- |
| `app/main.py`, `connections.py` | Room transport, presence, validation patterns, existing WS tests | Extract dispatch; stable seats; serial transactions; current active-player blanket check cannot gate reactions |
| `app/rules/types.py`, `registry.py`, `saga_core.py` | Module discovery and passive manifest | Executable runtime, capability/version contracts; classify metadata as provisional |
| `validate_unit_state` and `Unit` | Basic ID/type/owner shape | Separate recruitment from in-game validity; current minimum rejects surviving sub-four units; per-figure geometry |
| Default A/B tokens and ownerless Warlords | Sandbox fixtures | Real roster/deployment and ownership; no seeded demo figures in enforced games |
| 800 x 500 mm board, whole-mm tokens | SVG viewport and drag previews | Scenario-sized table and exact imperial measurement configuration; versioned fixed-point migration |
| d20 initiative, winner chooses order | Sandbox flow only | Clash d6 first player and explicit tie adaptation; no choice of first/second in that scenario |
| Connection-list turn rotation and disconnect auto-pass | Presence notifications | Fixed seat order; pause/rejoin without changing turn; keep games when sockets close |
| `ACTIVATE_TOKEN` counters | Sandbox markers | Activation grant/cost/resolution; separate counters for rest, repetition, consecutive shooting, cancelled actions |
| `ROLL_DICE` count <=20 | RNG service seed implementation | Structured rule rolls, ordinary/SAGA distinction; melee may roll 32 attack dice |
| Terrain manifest `adds_fatigue_on_entry`, generic cover/LOS booleans | Discovery API shape only | Finishing versus crossing; independent height/difficulty/cover/size and geometry queries |
| Manifest `melee-reaction`, `survival_points`, `slaughtering_points` | Existing IDs need compatibility handling | Core keyword is Melee for either role; Clash uses massacre scoring; verify/replace labels with schema migration |
| Timing manifest `repeatable_per_turn` | Timing labels only | Usage limits belong to individual abilities and basic/advanced classification, not a shared timing keyword |
| `make_event` increments seq for private/shared responses | Envelope concept | Durable domain event cursor and state version separate from transport sequencing |
| Token-only undo | Sandbox feature | Transaction-aware safe undo; disable bypass in enforced play |
| `test_integration_smoke.py` | Transport regression suite | Currently tests only a bootstrap turn cycle; add real setup-to-result suite |
| App/Board generated types plus local parsers | Protocol generation and board controls | Remove duplicated shapes incrementally; add runtime validation and browser tests |

No source, schema, or runtime behavior changes in this planning branch. Update `docs/protocol.md` and `docs/data-model.md` when implementing their actual changes, not as though these proposals are already live.

## Milestones and dependency order

| Milestone | Packages | Demonstration |
| --- | --- | --- |
| M0: Reliable substrate | P00-P03 | Versioned source/config, deterministic commands, stable seats, legal roster and exact figure geometry |
| M1: Setup and orders | P04-P07 | Legal terrain/deployment, pregame dice, both Orders reaction windows, persisted choices |
| M2: Full core actions | P08-P11 | Movement/rest, shooting, charges/melee/withdrawal, fatigue and all core equipment/special rules |
| M3: Complete supported game | P12-P13 | Approved generic gameplay content and all core scenario end/chaos/scoring paths; faction packs follow later |
| M4: Release-ready online play | P14-P15 | Durable recovery, full browser game, replay agreement, verified source questions/content |

Dependency graph (an arrow means prerequisite):

```mermaid
flowchart LR
    P00 -->|baseline P00.1| P01 --> P02 --> P03 --> P04
    P01 --> P05
    P02 --> P05
    P05 --> P06
    P04 --> P07
    P06 --> P07
    P03 --> P08
    P04 --> P08
    P05 --> P08
    P06 --> P08
    P08 --> P09 --> P10 --> P11
    P07 --> P12
    P11 --> P12
    P07 --> P13
    P11 --> P13
    P12 --> P13
    P13 --> P14 --> P15
```

This is a safe default execution order, not a request for concurrent work. Specify the generic activation/board model in P00 alongside the source-backed profiles and chosen loadouts; later faction source collection is independent of starting the engine. P01 establishes a storage interface early; P14 supplies production durability. Every package includes narrow UI and snapshot support, so P15 is integration work rather than the first frontend implementation.

## P00 - Source baseline and decisions

**Depends on:** none. **Covers:** provenance for all requirements, especially R01/R33.

1. `P00.1`: Create the machine-readable source/requirement registry from [coverage](rules-coverage.md), pin source hash, and record selected digital conventions. Preserve open questions as unresolved; do not claim official FAQ verification.
2. `P00.2`: Apply recorded owner rulings Q01-Q11 without reopening them, including corrected Q06 for source profiles and Q11 for Clash's declared unit count. Record the explicit source interpretations in coverage, including the p.26 pre-pool cap taking precedence over p.29's example. Start with the seven generic loadouts; record the still-needed generic board/activation specification. Collect named faction sources only for later packs; do not gate generic profile work on them.
3. `P00.3`: Add capability/source support status to module metadata design, confirm pack storage/validation format, and record the geometry/protocol/state decisions as ADRs when implementation begins.

**Touch:** `rules-roadmap/`, the source/requirement registry at `services/api/app/rules/provenance/data/`, `docs/adrs/`; metadata schema only if needed in that slice.

**Status:** `P00.1` complete: the registry indexes sources (CORE-2022 pinned by SHA-256), R01-R34, D01-D15/Q01-Q11, P00-P15 slices, and the selected measurement/tie-break conventions, validated by `services/api/tests/test_rules_provenance.py`. `P00.2` and `P00.3` remain.

**Exit:** every planned rule has a source and owner package; unresolved questions explicitly gate affected conformance. Do not defer a basic-engine design decision to “decide later” when this plan already selects a default.

## P01 - Command runtime, identity, event ledger

**Depends on:** P00.1. **Covers:** R27-R30/R32 foundation.

1. `P01.1`: Extract dispatch from the WS loop, introduce deterministic reducer and in-memory event-store adapter; preserve sandbox regression behavior. Add explicit sandbox/enforced routing boundary.
2. `P01.2`: Stable seats and private resume credentials; separate presence/spectators; fixed seat order; enforced rooms pause on disconnect and survive empty connections.
3. `P01.3`: Per-room serialized transactions, typed schema validation, dedupe receipts checked inside the transaction, expected versions, domain event cursor, full snapshot/resync, injected RNG interface. Verify both generators preserve the schema constructs introduced, including mixed required/optional fields; generated types alone do not validate incoming JSON.
4. `P01.4`: Block legacy token/roll/undo commands from bypassing enforced rules; protocol-version handshake for changed identity/envelopes.

**Touch:** `app/main.py`, `connections.py`, new `app/engine/`, `app/commands/`, schema/generators, web connection/store, transport tests.

**Exit/tests:** duplicate accepted command has one result and one RNG consumption; malformed/unauthorized/stale intents cannot mutate; retry is recognized before stale-version check; concurrent clients cannot spend the same resource; rejoin preserves ownership/turn; private traffic cannot create false replay gaps. Existing sandbox tests pass. Full durability is still explicitly pending P14.

## P02 - Profiles, warbands, figures, and roster UI

**Depends on:** P01. **Covers:** R02-R03, R20/R24 model.

1. `P02.1`: Implement the four CORE-2022 base profiles and seven chosen generic loadouts first. Store immutable base Armour and rational melee/shooting Aggression, inherited special-rule IDs, and generation thresholds; derive equipment modifiers and the Levy no-ranged-weapon melee exception separately. Register all six Warlord rules and horse/bow policies for full enforcement in P08-P11. Keep Hero class/Warlord role and physical/effective counts distinct. Preserve legacy manifest compatibility through versioning.
2. `P02.2`: Recruitment ledger, point bundles/single exchange, faction validation hooks, unit organization, individual figure/base state, stable owners. Undeployed figures belong to the recruitment pool; original unit identity/count becomes immutable on deployment commitment.
3. `P02.3`: Roster editor/import validation and unit inspection. Ordinary surviving count permits 1..3; destroyed units retain ledger identity and cannot act.

**Touch:** rules/domain state and schema; new roster tests/components; default room fixture construction.

**Exit/tests:** no ownerless deployed units; valid and invalid budgets/groupings; exact one Warlord; profile versus equipment legality; subminimum survivors; undeployed recruitment pool can form legal units during scenario steps; committed units cannot be retroactively regrouped. Generic Levies without ranged weapons derive Armour 4 / 4 and melee Aggression 1/2; bow Levies derive Armour 3 / 3 and melee Aggression 1/3, with shooting Aggression 1/2. Mounted Warlord/Hearthguard Armour derives 5 / 4 once from base 5. All six Warlord rule IDs and troop generation thresholds are present; shooting stats do not grant ranged actions. The approved generic roster is available for preview/configuration; enforced play stays gated on complete pack/scenario capabilities in P12/P13. Synthetic fixtures remain internal to conformance tests.

## P03 - Exact geometry and formation

**Depends on:** P02. **Covers:** R01/R04 and queries for R05/R14-R19.

1. `P03.1`: Fixed-point conversion, C-to-S distance normalization, and band/inch measurements, circular/nonround bases, within/entirely-within predicates, board bounds. Version coordinates once; render all measurements from the same config.
2. `P03.2`: Connected formation graph, reference validation, ordered placements with distinct ordinary-move/charge/deployment neighbor checks, obstacles/inter-figure barriers, swept corridors and end rotation.
3. `P03.3`: LOS segment/terrain queries, deployment-region helpers, bounded deterministic contact/withdrawal feasibility approach with documented numerical tolerance and adversarial tests.
4. `P03.4`: Board renders individual bases and selection/group previews; add read-only ruler/range/formation diagnostics and non-drag placement inputs.

**Touch:** new `app/geometry/`, policy adapters in rules, `Board.tsx`, geometry fixtures/tests.

**Exit/tests:** threshold equality/one quantum either side for exact imperial bands and inch distances; rotations cannot create movement; no path tunneling; disjoint clusters fail; source/target edge sight; deterministic placements. P03.3 must demonstrate feasibility checking, not label a heuristic failure “impossible.” No aggregate-unit-footprint shortcut for enforced play.

## P04 - Terrain engine and catalog

**Depends on:** P03. **Covers:** R05, terrain portion R06.

1. `P04.1`: Independent traits and curated footprints; all seven Clash presets; impassable primitives; size/count restrictions using the owner-confirmed S minimum small-terrain width (Q01).
2. `P04.2`: Path-wide unit restrictions, partial/full containment, high-terrain sight queries, terrain fatigue hooks and horse-specific contribution.
3. `P04.3`: Terrain placement preview, authoritative rejection reasons, trait/cover overlay, setup locks.

**Touch:** rules terrain policies/catalog, geometry tests, schema, board terrain UI.

**Exit/tests:** crossing versus finishing; one figure slows whole unit; no cover from partial containment; hill blocks through-sight without slowing; rocky ground slows/protects without height; large-only/count rules; dangerous and uneven remain distinct traits.

## P05 - Resolutions, choices, and ability primitives

**Depends on:** P01-P02. **Covers:** R08/R10-R12/R31 infrastructure.

1. `P05.1`: Serializable resolution stack, choice lifecycle, actor/role permissions, parent resumption, two-pass alternating window, empty-window progression.
2. `P05.2`: Typed ability costs, trigger IDs, restrictions, effect order/dependencies, captured/deferred values, durations, explicit overrides; deterministic RNG continuations. Carry the combat rule coupling ability prohibitions to fatigue use, with the explicit mercenary exception; distinguish it from having no allocated ability dice.
3. `P05.3`: Generic pending-choice/priority panel, effect ordering UI, read-only opponent state, resync during nested choice.

**Touch:** engine resolutions, rules effects/timings, schema, choice UI, unit/integration tests.

**Exit/tests:** nonactive player can respond only to owned choice; duplicate/stale/wrong-trigger responses fail; pass/act/pass/pass works; one Activation/Reaction per occurrence; effects use correct priority and duration; no callback/closure in snapshot. Core runtime does not inspect faction names.

## P06 - Turn and Orders/SAGA dice

**Depends on:** P05 and P02. **Covers:** R08-R10, R01 dice arithmetic.

1. `P06.1`: Turn IDs/counters and explicit Orders substates, generation query, exactly-eight inventory, retained allocation reclaim, initial symbol roll.
2. `P06.2`: Allocation cost groups, Orders effects/extra rolls, two opponent reaction windows, basic/advanced placement and trigger limits.
3. `P06.3`: End-Orders cleanup, retained allocations, turn expiry/reset, board/dice tray and phase controls. Expose scenario turn-start/end hooks; P13 supplies complete termination.

**Touch:** rules turns/dice/abilities, schema/events, board panel/phase UI.

**Exit/tests:** threshold changes after casualties; no ninth die; reclaim all of multi-cost; carry-over/reallocate/trigger counters; independent ordinary/SAGA rerolls; active effects and fatigue survive appropriate boundaries; cannot activate during Orders.

## P07 - Complete setup flow

**Depends on:** P04 and P06. **Covers:** R03/R06-R07, R26 setup.

1. `P07.1`: Game configuration and both-player option agreement, recruitment totals with unassigned troops, correct table/edges, Clash first-player procedure with coin-toss tie-break.
2. `P07.2`: Alternating terrain placement, legal reposition after three, opponent final offer, immutable terrain lock.
3. `P07.3`: Deployment die/adjustment and A/B/C zones; scenario-defined quotas and order. For Clash, record the first player's declared final N including Warlord, require ceil(N/2) in the first batch including Warlord, then opponent-all and floor(N/2) remainder (Q11). Form units and select equipment at each opportunity; validate every figure and feasibility of the remaining pool/count. Do not impose this sequence/count declaration on other scenarios or freeze future unit groupings.
4. `P07.4`: Second-player three-die pregame allocation, chaos setup hooks, readiness/start barrier. Provide full setup wizard and step back only before its committed/revealed boundary.

**Touch:** scenario setup module, state/schema, setup wizard, geometry/integration tests.

**Exit/tests:** both edge orientations for each method; odd/even declared count and quota; reject impossible remaining partition; no out-of-zone base sliver; no missing figure; no pregame ability triggering; wrong setup actor rejected. The start transition enters actual Orders when selected capabilities are complete; until then exercise it only with internal fixtures, not a falsely playable generic pack.

## P08 - Movement, rest, manoeuvre, fatigue

**Depends on:** P03-P06. **Covers:** R12-R14; charge declaration skeleton R15.

1. `P08.1`: Validated activation grants, separate all-action/MCS/last-kind histories, cancellation, multi-unit queue, opponent fatigue-cancellation gate before Activation/Reaction. Cancelled attempts consume costs/free use but open no reaction window; Old Grudge entitlement is consumed separately from resolved-action history.
2. `P08.2`: Movement proposals and atomic route/formation commit; terrain/fatigue interactions; manoeuvre; preview/confirm/cancel UI.
3. `P08.3`: Rest, exhaustion/cap, repetition timing, nearby destruction fatigue handler, no-fatigue versus free semantics; fatigue and activation status UI.

**Touch:** activations/fatigue/movement rule handlers, schema, board actions/choice panel.

**Exit/tests:** all R12-R14 cases; rest then move; cancelled grants; two-fatigue cancellation including rest; optional fatigue reduction to S; enemy-turn histories; manoeuvre throughout path; repeat+terrain stacking. Do not expose charge as complete until P10 or shoot until P09.

## P09 - Shooting vertical slice

**Depends on:** P08 (and P03-P06). **Covers:** R16-R17/R20, ranged parts R22.

1. `P09.1`: Weapon/range/LOS eligibility with sight-specific third-party gap policy, single target, reaction revalidation, unitless source shape; show per-figure eligibility.
2. `P09.2`: Initial/bonus pool caps, ability/fatigue window, ordered attack/defence RNG/effects, automatic hits, cover and Armour.
3. `P09.3`: Prevention extension hooks, owned casualty choices/cohesion, loss/destruction ledger, post-shoot fatigue and complete combat summary. Special prevention implementations arrive P11.

**Touch:** shooting resolver, dice/effects/casualties, UI target/combat/casualty controls, focused WS tests.

**Exit/tests:** scripted dice make expected losses; stage caps and fractional aggression; no sight after reaction cancels without refund; choose out-of-range casualty; no client-defined hit totals; reconnect in every step; unitless restrictions. A deterministic fixture battle can finish a shot with no manual intervention.

## P10 - Charge, melee, withdrawal vertical slice

**Depends on:** P09 (reuses pool/loss infrastructure). **Covers:** R15/R18-R20.

1. `P10.1`: Charge placement/contact solver, fixed reference, mandatory approach, reaction revalidation and cancellation rollback; apply repetition/terrain fatigue before melee.
2. `P10.2`: Close ranks and solid-cover consequences, both pools with explicit pre-pool figure/natural-dice limits, alternating effects/fatigue, latched exhaustion, simultaneous attack/defence handling, ordered casualty selection and contact preservation.
3. `P10.3`: Outcome calculation, end fatigue, withdrawal obligation and validated blocked-route fallback; complete placement UI and resume at every choice.

**Touch:** charge/melee/withdrawal policies, geometry solver, ledger, UI, regression fixtures.

**Exit/tests:** each R15/R18/R19 case, including failed last figure, 32 dice, early destruction versus contact break, odd closed-ranks pool, mutual annihilation, protected defender forcing retreat, blocked withdrawal and alternate separation. No completed melee leaves units illegally touching.

## P11 - All core special rules and equipment composition

**Depends on:** P10. **Covers:** R21-R24; completes prevention and profile exceptions.

1. `P11.1`: Determination, We Obey, Presence, Pride; individual counters and explicit count query policies.
2. `P11.2`: Resilience, Bodyguards, Heroic Unit with prevention/redirection/swap choices; apply resolved Q02/Q04, including exchanges reaching exhaustion and Presence limited to SAGA abilities.
3. `P11.3`: Every R22/R23 equipment behavior; consecutive-shot history, horse penalties/overrides, javelin grant. Apply corrected Q05: charge-only timing and no close ranks for Improvised Projectiles, bows/slings, javelins, crossbows, horse mounts, heavy weapons, or Unarmed. Preserve composite bows and other sourced restrictions; eligibility combines definition-level prohibitions rather than a closed equipment list.
4. `P11.4`: Core mercenary/Legendary restrictions and support flags, composition tests against terrain, fatigue, scoring, and abilities; source-less profiles remain test-only.

**Touch:** rule primitives/definitions, roster validation, choice UI, cross-rule regression tests.

**Exit/tests:** all listed rules work, not just manifests; prevention does not truncate incoming Hero casualties; Bodyguards cannot bounce; cancellation consumes free uses; mounted/weapon combinations validated; mercenary fatigue exception remains usable. No generic transport branch named after a special rule.

## P12 - Generic gameplay content, then faction extensions

**Depends on:** P07/P11; generic profiles start P02 and board specification starts P00. **Covers:** R03/R10/R24/R33.

1. `P12.1`: Complete the generic pack using its approved activation/board specification, with version/hash and capability validation. Profiles alone do not define costs/abilities; report missing specification rather than inventing it. Both players may use this shared pack.
2. `P12.2`: For every ability record source, costs, timing, restrictions, use limits, ordered effects, choices, duration, overrides, and interaction tests. Implement any missing primitive with focused tests before enabling that ability.
3. `P12.3`: All supported recruitment/equipment choices and dice-symbol mappings; complete original ability-panel UI; pack lint and generic-versus-generic conformance fixtures; add faction-specific suites when complete packs become available.

**Touch:** data packs, narrow rule handlers, manifest/schema as necessary, content tests and ability/roster UI.

**Exit:** the approved generic roster and activation/board content are playable for both seats. Every selectable item maps to implementation/tests; no disabled-but-selectable abilities or invented costs. Later faction packs require complete sourced lists/boards and every declared capability; named mercenary/Legendary choices require verified profiles. Missing faction sources do not block the generic milestone.

## P13 - Scenario completion, scoring, chaos

**Depends on:** P07/P11/P12. **Covers:** R25-R26/R34.

1. `P13.1`: Turn-start zero-generation loss and end after six turns each; score ledger calculation, ordinary/mercenary/Legendary bonuses, threshold/draw logic, concession.
2. `P13.2`: All six chaos outcomes, pregame/turn-duration effects and score interactions, mutual opt-in recorded in configuration.
3. `P13.3`: Immutable final result, per-category explanation, final board/history and rematch as a new game; reject gameplay after finish.

**Touch:** Clash scenario/scoring, turn hooks, UI results/options, scenario tests.

**Exit/tests:** boundary scores 7-0/8-7/8-6; sixth turn of second player completes; final effects before score; zero generated differs from no available dice; Warlord death alone does not finish; Judgement/Slaughter correctly included; simultaneous losses and redirected casualties score once.

## P14 - Durable save/resume, replay, safe undo

**Depends on:** P13; uses P01 contracts. **Covers:** R27-R30/R32/R34.

1. `P14.1`: Postgres event/snapshot/receipt store and migrations; atomically commit game changes; configurable retention independent of sockets; preserve pinned pack versions.
2. `P14.2`: Client reconnect/backoff, stable resume, full resync/gap recovery; pause while opponent disconnected; handle server restart mid-choice and commit-before-broadcast failure.
3. `P14.3`: Replay/export without credentials, deterministic hash checks, read-only spectators; safe deterministic negotiated undo or explicitly disabled committed undo in enforced play until its guarantees pass.

**Touch:** storage adapter/migrations/config, WS/client store, recovery/replay tests, operational docs.

**Exit/tests:** recover in every representative combat/setup/Orders checkpoint; expired/forged resume fails; duplicates across restart preserve rolls; process restart loses no committed game; old content cannot silently substitute; replay equals live final state. A restore-from-backup smoke check proves the configured durable path.

## P15 - Complete-game release verification

**Depends on:** P14 and all source/content gates. **Covers:** R01-R34 integration.

1. `P15.1`: Browser acceptance coverage for both seats: roster/setup, dice/abilities, movement/combat/choices, result, refresh/reconnect. Every required action has a usable non-console control.
2. `P15.2`: Run [release scripts](validation-and-release.md) using the generic pack (and later any added faction packs), all deployment methods, equipment/special-rule cases, each chaos result, score/draw/automatic loss/concession, and interrupted play.
3. `P15.3`: Reconcile coverage registry, source rulings, feature support flags, protocol/model/context docs, and troubleshooting; remove internal-only test data from selectable content. Re-run required CI checks after final fixes.

**Exit:** every release checklist item is satisfied with evidence. Fixture-only, backend-only, manual-score, unspecified-activation-economy, or unrecoverable games do not meet this milestone. Expansion work starts with a new source/coverage plan rather than expanding this release without updating its criteria.

## Status tracking

At planning time P00-P15 are not complete. Existing passive modules/units only reduce some scaffolding work. Record slice status in `services/api/app/rules/provenance/data/work_packages.json` and requirement status/evidence in `requirements.json`. For each slice also record prerequisite versions, changed paths, requirement/test links, manual demonstration, unresolved decisions, and exact next slice. Mark a package complete only when all its exit criteria pass. Use `source_blocked` for the affected behavior without blocking independent engine tasks.
