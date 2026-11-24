# Decisions and Source Gaps

This register separates engineering choices from source-backed mechanics. It is part of the implementation plan, not a claim that any code has changed. The project owner's Studio Tomahawk authorization is recorded; do not reopen general permission as a prerequisite to mechanics implementation. Keep repository source-handling boundaries from AGENTS.md.

## Selected engineering defaults

These defaults make the work executable. Change one only with a recorded rationale, affected requirement/test updates, and an ADR when implementation starts.

| ID | Decision | Rationale / implementation consequence |
| --- | --- | --- |
| D01 | Two fixed player seats; optional spectators cannot issue gameplay commands | Connection ordering must not define ownership, turn order, or reaction permissions. P01 introduces private resume credentials; full accounts are not required. |
| D02 | Individual figures are authoritative; group movement is a UI convenience | Cohesion, LOS, contact, terrain, casualty choices, and withdrawal cannot be faithfully implemented with one unit token. |
| D03 | Fixed-point 0.1 mm coordinates; per-game metric or imperial rulers/table; default imperial to continue existing rules-facing conventions | Exact inch conversions are preserved; metric is a distinct rules mode. Protocol changes are versioned, not silently applied to existing integer-mm fields. Numerical geometry policy must be documented/tested in P03. |
| D04 | Clash uses server d6 for first player; reroll tied d6 values | This is an explicit digital replacement for p.48's social tie-break. Record `clash_tie_break=reroll_d6` in configuration and show it before readiness. It is not the book's printed tie procedure or the current d20/winner-choice flow. |
| D05 | Lock a complete unit organization before computing first-player deployment quota | Recruitment may be grouped during setup, but changing the eventual number of units after placing the first half would make the quota ambiguous. Preserve deployment order and equipment/faction legality; disclose the lock in the wizard. |
| D06 | Pause on player disconnect, retain room, no implicit auto-pass/forfeit/deadline in casual mode | Pending opponent decisions are rules state. Resume exact phase/choice; timed modes require separate pregame policy. |
| D07 | Sandbox remains available; enforced rooms reject legacy command bypasses | Preserve bootstrap tests while adding the runtime. Do not interpret sandbox success as SAGA conformance. |
| D08 | Deterministic reducer plus serialized transactions, recorded RNG, dedupe receipts | Reconnect/retry/replay must not reroll, double-spend, or erase opponent choices. Separate domain cursor from transport messages. |
| D09 | In-memory store adapter first, Postgres durability before release; one writer per room | Matches existing architecture direction without requiring distributed infrastructure. Accounts/matchmaking/Redis are outside this engine milestone. |
| D10 | Declarative versioned content packs plus reviewed effect handlers; no arbitrary imported executable code | Validate capabilities, references, limits, source provenance, and version compatibility before selecting a pack. |
| D11 | Ordinary actions use owner decisions, not an automatic casualty or withdrawal policy | Automatic defaults may be suggested but cannot replace a legal player's choice. Empty reaction windows may progress automatically with evidence. |
| D12 | Committed undo disabled in enforced games until full transaction compensation is safe | Preview/cancel remains. Later negotiated undo cannot cross random information, reactions, or choices. Token-only rollback is not sufficient. |
| D13 | First release = complete core book + two complete compatible faction packs | Core-only fixtures are useful for tests but do not satisfy playable SAGA. Every selectable pack item must work; expansion books are separate milestones. |
| D14 | Curated valid terrain/base shapes first, original functional ability UI | Exact geometry and complete mechanics precede an unrestricted terrain editor. No dependency on published board artwork or model art. |
| D15 | Concession is an explicit terminal intent from either seat | A digital product feature; distinguish it from scenario scoring, zero-generation defeat, and disconnection. |

## Source questions and resolution gates

A question is resolved by attaching an applicable official correction/clarification to the source registry, or recording a maintainer-approved interpretation as a named variant. Do not invent an answer from another edition. Source selection may change values, but must not silently change games already pinned to an older version.

| ID | Evidence / uncertainty | Required action and gate |
| --- | --- | --- |
| Q01 | CORE-2022 p.35's small-terrain minimum width is printed as `C`, absent from the English VS/S/M/L definitions. The maximum small footprint and large minimum width are readable. | Check applicable official correction; confirm the intended band. Candidate S is an inference, not a verified rule. Gate P04 small-terrain conformance and release; geometry interface/large-shape work can proceed. |
| Q02 | p.36 Resilience states it cannot exhaust its user, while its parenthetical threshold wording and example can suggest a different boundary. This materially changes Warlord survival. | Confirm whether reaching exhaustion is prohibited or only exceeding it; test fatigue 0/1/2 with Resilience(1)/(2) and Bodyguards. Until resolved, use configurable test policies and no claim of conformance. Gate P11 and release. |
| Q03 | p.5 offers 2.5 cm or 1 inch ruler width; p.9 says width-dependent effects use 1 inch. | Confirm mode-specific width for metric play. Default imperial has unambiguous 25.4 mm width; gate any metric width-sensitive content, not unrelated distance geometry. |
| Q04 | p.36 Presence first mentions special rules or abilities, then narrows its scope to abilities; explicit exclusions cover ordinary counts, pool limits, and scoring. | Confirm scope for any special-rule interaction that actually needs effective model count. Keep physical/scoring counts separate regardless. Gate P11's affected interactions and dependent packs. |
| Q05 | p.39 Improvised Projectiles does not expressly forbid close ranks; p.51's equipment summary groups its entries beneath a blanket prohibition. Detailed chapters and summary differ in specificity. | Verify intended close-ranks rule before enabling that combination. Gate that equipment interaction in P11 and full-core release. |

P00 also records interpretation tests for timing combinations: fatigue cancellation versus Activation/Reaction priority, Old Grudge grants/cancellation during first turns, and unitless shooting pool exceptions. Reopen the detailed source before coding. If an ambiguity changes a player's legal options, add a new question here rather than concealing it in implementation. A declaration-only restriction must not be rerun at an arbitrary later stage: for example, fatigue gained during a valid charge does not cancel the ensuing melee, and exhaustion acquired during a shooting resolution does not itself restart activation legality.

## Missing content and scope boundaries

| Item | Why needed | Work that can proceed | Completion condition |
| --- | --- | --- | --- |
| Two faction Universes/lists and full battle boards, compatible revisions | Recruitment permissions, all ability costs/timings/effects, faction dice symbols | Core mechanics and original synthetic test packs | P12 verifies two whole boards/lists; each ability/profile references source and tests. |
| Applicable official FAQ/errata | Confirm baseline and resolve Q01-Q05; source may have later corrections | Versioned interfaces and tests parameterized by explicit policy | Record exactly which corrections apply; do not describe the source as current without checking. |
| Named Hero/mercenary/Legendary profiles desired for release | Core defines their framework, not their particular stats/costs/effects | Generic restrictions, profile hooks, scoring with fixtures | Only enable individually verified complete profiles; unavailable ones do not appear as usable roster choices. |
| Extra scenarios, building rules, multiplayer/campaigns | Book of Battles is referenced but not supplied | Scenario extension contracts and core ruins behavior | New source-backed coverage plan and pack-specific tests. |
| Creatures, elephants, other mounts, magic, Universe-specific subsystems | Core explicitly delegates their rules | Capability declarations and unsupported-content errors | Implement required capabilities and conformance suite before enabling a dependent faction/pack. |

A user statement of authorization is sufficient for this planning/implementation scope; source absence is a technical completeness issue, not a request to repeat permission. Packaging copyrighted prose or art is unnecessary for the planned engine and is not included here.

## Engineering risks and mitigations

- **Geometry complexity:** charge contact/maximal approach and blocked withdrawal require feasibility reasoning. Prototype these in P03 before investing in combat UI; P10 must pass adversarial fixtures. Do not label an unsuccessful heuristic search as impossible movement.
- **Effect-order explosion:** use typed contexts, explicit priorities, persistent choices, and tests for interacting primitives; do not build one permissive text-script interpreter.
- **False validation reuse:** deployment minimum sizes differ from surviving sizes; physical counts differ from Presence; cancellation differs from resolved activation. Keep separate queries and invariants.
- **Replay drift:** pin rules/content/schema versions, persist outcomes, maintain reducers or explicit migrations. Never reconstruct randomness or past geometry against new code silently.
- **Large implementation packages:** each numbered slice is an upper boundary; split further by behavior/protocol change using the playbook. Keep useful UI and tests in each slice.
- **In-memory loss before P14:** development demos are not durable yet. Release remains gated on crash/restart tests and database persistence.
- **Missing content discovered late:** collect sources in P00 while core work proceeds. Do not treat cropped sample abilities inside the core book as a complete faction board.
