# Decisions and Source Gaps

This register separates engineering choices from source-backed mechanics. It is part of the implementation plan, not a claim that any code has changed. The project owner's Studio Tomahawk authorization is recorded; do not reopen general permission as a prerequisite to mechanics implementation. Keep repository source-handling boundaries from AGENTS.md.

## Selected engineering defaults

These defaults make the work executable. Change one only with a recorded rationale, affected requirement/test updates, and an ADR when implementation starts.

| ID | Decision | Rationale / implementation consequence |
| --- | --- | --- |
| D01 | Two fixed player seats; optional spectators cannot issue gameplay commands | Connection ordering must not define ownership, turn order, or reaction permissions. P01 introduces private resume credentials; full accounts are not required. |
| D02 | Individual figures are authoritative; group movement is a UI convenience | Cohesion, LOS, contact, terrain, casualty choices, and withdrawal cannot be faithfully implemented with one unit token. |
| D03 | Fixed-point 0.1 mm internal coordinates; SAGA bands first, inches for other player-facing distances; imperial table/rulers only | Owner ruling Q03 selects VS/S/M/L = 2/4/6/12 inches and a 48 x 36 inch table. Internal/source dimensions may use exact mm conversion; no selectable metric rules mode is planned. Protocol changes are versioned, not silently applied to existing integer-mm fields. Numerical geometry policy must be documented/tested in P03. |
| D04 | Clash uses server d6 for first player; tied results use a fair heads/tails toss | Owner selected a coin toss (Q10). Record `clash_tie_break=coin_toss`, preassign heads/tails to the two stable seats, and persist the server result. This changes only the tie-break. |
| D05 | Organize units and choose allowed equipment during deployment | Owner ruling Q09 supersedes the former organization freeze. Keep an unassigned troop pool; lock units individually when deployed. The selected scenario supplies quota/counting rules and deployment sequence. |
| D06 | Pause on player disconnect, retain room, no implicit auto-pass/forfeit/deadline in casual mode | Pending opponent decisions are rules state. Resume exact phase/choice; timed modes require separate pregame policy. |
| D07 | Sandbox remains available; enforced rooms reject legacy command bypasses | Preserve bootstrap tests while adding the runtime. Do not interpret sandbox success as SAGA conformance. |
| D08 | Deterministic reducer plus serialized transactions, recorded RNG, dedupe receipts | Reconnect/retry/replay must not reroll, double-spend, or erase opponent choices. Separate domain cursor from transport messages. |
| D09 | In-memory store adapter first, Postgres durability before release; one writer per room | Matches existing architecture direction without requiring distributed infrastructure. Accounts/matchmaking/Redis are outside this engine milestone. |
| D10 | Declarative versioned content packs plus reviewed effect handlers; no arbitrary imported executable code | Validate capabilities, references, limits, source provenance, and version compatibility before selecting a pack. |
| D11 | Ordinary actions use owner decisions, not an automatic casualty or withdrawal policy | Automatic defaults may be suggested but cannot replace a legal player's choice. Empty reaction windows may progress automatically with evidence. |
| D12 | Committed undo disabled in enforced games until full transaction compensation is safe | Preview/cancel remains. Later negotiated undo cannot cross random information, reactions, or choices. Token-only rollback is not sufficient. |
| D13 | First implementation target: generic warband with owner-selected loadouts | Use the four source-backed base profiles and seven derived loadouts in generic-warband.md, including every inherited troop/equipment rule. A complete generic game also needs an explicitly specified generic board/activation economy. Named faction packs follow later; their sources no longer block initial implementation. |
| D14 | Curated valid terrain/base shapes first, original functional ability UI | Exact geometry and complete mechanics precede an unrestricted terrain editor. No dependency on published board artwork or model art. |
| D15 | Concession is an explicit terminal intent from either seat | A digital product feature; distinguish it from scenario scoring, zero-generation defeat, and disconnection. |

## Owner rulings and remaining source questions

The project owner supplied the following rulings on 2026-11-24 (`OWNER-2026-11-24`). They are authoritative for this project and take precedence over conflicting or ambiguous source wording. Q01-Q10 are resolved; do not require another confirmation or an erratum before implementing them. Q05 records both the timing and equipment-eligibility rulings. Q06 includes the latest correction: use the rulebook's base profiles and special rules instead of the earlier numerical statements, including the earlier equal-Armour answer for Levies. Other rulings remain in effect. Preserve these IDs for traceability. Future source changes must not silently change games already pinned to a version.

| ID | Evidence / uncertainty | Required action and gate |
| --- | --- | --- |
| Q01 | **Resolved by owner:** C is the translated distance label for S. | Normalize C to S wherever it denotes a distance; small-terrain minimum width is S (4 inches). Preserve unrelated labels such as deployment Method C. No source gate remains. |
| Q02 | **Resolved by owner:** Resilience(X), called Resistance(X) in the clarification, trades up to X casualties for one fatigue if the receiving unit is not exhausted before that exchange. | Reaching the exhaustion threshold is legal; once exhausted no further exchange is legal. Recheck before each exchange. Resilience(1) at fatigue 2 with cap 3 can cancel one casualty and reach 3; at 3 it cannot cancel another. Resilience(2) cancels one or two casualties for the same one fatigue. Use canonical Resilience in definitions; no source gate remains. |
| Q03 | **Resolved by owner:** use VS/S/M/L = 2/4/6/12 inches; use inches when a band is unavailable. | Use the imperial 48 x 36 inch table and 1 inch ruler width. Preserve exact internal conversions and source-defined base dimensions; show player-facing distances as bands/inches. Metric rules mode is outside this plan. No source gate remains. |
| Q04 | **Resolved by owner:** Presence applies only to SAGA abilities, nothing else. | Enable effective count four only when evaluating applicable SAGA ability effects/targets. Special rules, geometry, ordinary combat-pool figure caps, recruitment, and scoring use actual counts. No source gate remains. |
| Q05 | **Resolved by owner:** close ranks is only a defender choice against a charge, never a reaction to a ranged attack. A unit with Improvised Projectiles can close ranks when charged, assuming no other restriction applies. | Reject close-ranks intents in every shooting window. At the melee close-ranks step, Improvised Projectiles does not disqualify the defender; retain independent restrictions such as being mounted or unarmed. No source gate remains. |
| Q06 | **Resolved by owner, corrected:** begin with a generic warband using the chosen seven loadouts, but take actual troop values and all special rules from CORE-2022 pp.44 onward and referenced equipment sections. | Follow [generic-warband.md](generic-warband.md): a single base Armour per troop profile, exact melee/shooting Aggression, inherited rules, and derived equipment effects. Levies have base Armour 4 and Aggression 1/3 melee / 1/2 shooting; having no ranged weapon changes melee to 1/2. Bows derive Armour 3 in both contexts; horses derive 5 melee / 4 shooting for Warlord/Hearthguards. Warriors have shooting Aggression 1/2. Earlier numerical overrides are superseded. |
| Q07 | **Resolved by owner:** opponent cancellation precedes Activation/Reaction eligibility. | A fatigue-cancelled attempt creates no Activation/Reaction opportunity. Dice or free use remain spent; resolved activation history is unchanged. |
| Q08 | **Resolved by owner:** Old Grudge follows the same cancellation-cost rule. | A cancelled free attempt consumes its free opportunity. Distinguish consumed grant from resolved activation. |
| Q09 | **Resolved by owner:** players organize their troops during deployment, reacting to prior placements. | Scenario instructions determine order and how quotas are counted. No universal half-army formula or requirement to freeze all future units. Each already-deployed unit stays committed. |
| Q10 | **Resolved by owner:** heads/tails replaces the proposed d6 tie reroll. | Preserve the initial scenario d6 roll; for tied results use one audited server coin toss with outcome-to-seat assignment fixed beforehand. |

P00 records regression tests for the now-settled cancellation priority and Old Grudge consumption, and interpretation tests for source-specific unitless shooting pool exceptions. Reopen the detailed source before coding. If an ambiguity changes a player's legal options, add a new question here rather than concealing it in implementation. A declaration-only restriction must not be rerun at an arbitrary later stage: for example, fatigue gained during a valid charge does not cancel the ensuing melee, and exhaustion acquired during a shooting resolution does not itself restart activation legality.

## Missing content and scope boundaries

| Item | Why needed | Work that can proceed | Completion condition |
| --- | --- | --- | --- |
| Generic battle board / activation economy | Starter loadouts and source profiles are settled; symbol costs and a full ability set are still needed | Generic roster and core engine implementation | Specify the shared generic board/cost model before complete-game acceptance; no invented unlimited activations. |
| Named faction lists and complete boards | Later faction-specific recruitment, costs/effects, dice symbols | Generic warband implementation proceeds independently | Validate each complete sourced pack before making it selectable; not an initial implementation gate. |
| Applicable official FAQ/errata | Check for additional applicable corrections; Q01-Q10 already have owner rulings | Versioned interfaces and tests parameterized by explicit policy | Record exactly which corrections apply; do not describe the source as current without checking. |
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
- **Missing content discovered late:** specify generic activation content in P00 while core work proceeds; obtain faction sources for later packs. Do not treat cropped sample abilities inside the core book as a complete faction board.
