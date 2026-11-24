# Validation and Release Gates

This specifies tests to add during implementation. The planning branch changes documentation only; it does not add or claim these tests. Use [R01-R34](rules-coverage.md) for coverage and P00-P15 for work ownership.

## Test layers and locations

| Layer | Purpose | Proposed location |
| --- | --- | --- |
| Pure rules | Recruitment, phase guards, dice inventory, fatigue, ability/equipment composition, scoring | `services/api/tests/rules/` |
| Geometry | Bases, distances, cohesion, corridors, sight, terrain, contact/withdrawal feasibility | `services/api/tests/geometry/` |
| Engine invariants | Reducer, replay, deduplication, serial transactions, versions, choices | `services/api/tests/engine/` |
| Protocol/WS | Two seats, out-of-turn choices, snapshot/resync, malformed/stale/unauthorized requests | Existing API test structure, new focused files |
| Persistence | Crash/restart, transaction commit/broadcast gap, pinned versions, restore | Tests using a disposable database |
| Content conformance | All selected profiles, loadouts, abilities, capabilities and source references | `services/api/tests/rules/packs/` |
| Web units/components | Event projection, choice owner, dice selection, placement previews, reconnect state | Establish a web test runner in a focused P01/P05 slice |
| Browser integration | Two browser contexts through setup, combat and results; reload/rejoin mid-choice | Establish Playwright or equivalent in a focused infrastructure slice, then `apps/web` integration tests |

Choose/add test dependencies deliberately when the relevant implementation begins. Do not introduce a test framework merely to check this documentation change. Retain existing bootstrap tests in sandbox mode; their “complete game” naming does not make them SAGA end-to-end coverage.

## Required invariants

Assert these after every accepted command and event reduction in test sequences:

1. Every recruited figure belongs to exactly one stable seat and either its unassigned recruitment pool or one committed unit. Deployment transfers it atomically from pool to unit. Record the permitted pre-organization exchange in the recruitment ledger; lock original unit membership/counts when deployment commits. Destroyed figures cannot act or return to the pool.
2. Eight SAGA dice per player, exactly one location each; allocations are complete valid cost groups. No duplicate die can pay two abilities.
3. No partial transaction: invalid proposals leave gameplay state unchanged. Legitimate rule cancellation is a recorded outcome with the appropriate costs/history.
4. Fatigue is within the profile's cap; exhaustion matches the count; histories belong to a specific player turn and distinguish kinds.
5. Accepted completed placements obey base bounds, obstacles, cohesion, and required contact/separation. Temporary previews do not enter authoritative snapshots as completed moves.
6. At most one actionable top-of-stack resolution; only its choice owner/priority seat may answer. Child effects preserve the parent continuation.
7. Each command receipt, random roll, casualty, and destruction is applied once. State version and domain cursor are monotonic in their own domains.
8. Effects expire at the specified checkpoint, and simultaneous effects obey role/player ordering.
9. Terminal state has one immutable result and rejects subsequent gameplay intents.
10. Full replay and snapshot-plus-tail replay produce the same canonical state/result hash as live execution, without randomness or geometry search during replay.

Use property/stateful tests where these invariants explore meaningful command sequences: generated legal/illegal moves, retries, effects, turn changes, and disconnects. Do not substitute broad random tests for explicit source cases.

## High-value regression examples

All examples below are original test arrangements. The Warrior-archer example uses a CORE-2022 equipment fixture outside the selectable generic pack (which has no Warrior bow option); its base Warrior profile is shared with that pack. Script RNG through a server test adapter; never add a production command that accepts desired rolls.

| Area | Test fixture and expected assertion |
| --- | --- |
| Fractional shooting | Five eligible Warrior shooters contribute ceil(5/2)=3 dice. Pre-pool +2 gives starting pool 5; a later +9 is limited to 10 total attack dice. |
| Melee pre-pool limits | Four Hearthguards generate eight natural dice. A pre-pool grant of seven bonus dice is limited to four by actual figure count, giving twelve before closing ranks/cap. Presence does not increase that limit. Later bonuses use the separate twice-starting-pool rule. |
| Unitless shooting | A synthetic source expressly grants twelve bonus attack dice with no shooting unit. Its source policy resolves those twelve without a fake figure count or zero-natural-pool cap; reject additional attack dice from SAGA abilities. Verify ordinary unit pool limits independently. |
| Base profiles and derived Armour | Assert the four source profiles and all seven chosen loadouts. Base Armour is 5 for Warlord/Hearthguards, 4 for Warriors/Levies. Horses derive 5 melee / 4 shooting; foot Levies without ranged weapons derive 4 / 4 and bow Levies 3 / 3. Repeated queries and deployment draft equipment changes preserve base values and apply each modifier once. |
| Levy Aggression exception | Five bow Levies contribute ceil(5/2)=3 ranged dice and ceil(5/3)=2 melee dice; five Levies without ranged weapons contribute ceil(5/2)=3 melee dice. All Levies retain base shooting Aggression 1/2; that characteristic alone grants no shooting action. |
| Inherited rules | Both Warlord loadouts carry Determination, We Obey, Presence, Bodyguards, Pride, and Resilience(1), with R21 behavior checks. Hero classification alone does not confer Heroic Unit. Bows/horses forbid close ranks; horses deny cover and apply formation, movement, and terrain-fatigue rules. |
| Deployment choices | In Clash, declare N=7 including Warlord, deploy four units including Warlord, then opponent-all, then three remaining units. With N=6, use three and three. Choose sizes/equipment at each opportunity. Reject an infeasible initial N and a commitment that strands figures or makes the remaining unit slots impossible. Preserve totals and committed placements without freezing future groupings. |
| Cancel before reaction | A charge cancelled using fatigue spends its paid/free grant and creates no Activation/Reaction window; resolved history stays unchanged. Duplicate cancellation cannot spend fatigue twice. |
| Old Grudge cancellation | Cancel a free first attempt; its free entitlement is consumed. A later attempt needs another valid grant, while its resolved-action counter still starts at zero. |
| Coin tie-break | Tied d6 results invoke one fair server heads/tails draw with preassigned seats; non-ties do not. Retry/replay preserves the original result. |
| Close ranks | Offer only to the eligible defender after a charge; reject in all shooting windows, even when the unit would otherwise be eligible. A defender's initial five-die pool discards ceil(5/2)=3, leaving two before the sixteen-die cap; later total cannot exceed four absent explicit override. |
| Ordinary rerolls | One die is rerolled once by attacker and then once by defender; a second reroll by either same player is rejected; ordered modifiers/results are auditable. |
| Carry-over allocations | An advanced Orders ability retains its allocation into a new turn, triggers, is allocated again, and cannot trigger twice that turn. |
| Generation | Surviving Hearthguard unit of one generates; Warriors three do not/four do; Levies five do not/six do. All eight dice already allocated is not zero generation. |
| Rest and repetition | Rest, move, move: rest removes one; first move adds no repetition fatigue; second adds one. A cancelled intervening action changes neither resolved history nor consecutive-shot eligibility. |
| Fatigue composition | A horse unit with previous MCS activation ends a new move in dangerous terrain: repetition, horse terrain, dangerous terrain are distinct causes, final count capped at exhaustion. |
| Fatigue and ability prohibition | A combat effect forbidding SAGA abilities also blocks that player's combat fatigue use. Merely having no allocated dice does not. The explicit mercenary fatigue exception remains available. |
| Formation | Two clusters each having a close neighbor but no connected VS chain fail. Removing the only bridging figure as a casualty fails when another valid loss choice exists. |
| Intermediate cohesion | Ordinary movement can use a still-unmoved unit member as its VS neighbor while meeting the first-mover radius and final formation checks. The equivalent charge placement requires an already moved neighbor. First deployment figure and lone Hero need no prior neighbor. |
| Path legality | Clear endpoint beyond an intervening terrain/unit barrier is rejected; own-unit figures may be crossed; other-unit gaps have their specific blocking policy. |
| Sight versus movement gaps | A third-party unit's gap can block sight even above movement's S/M threshold; firing/target-unit gaps are exempt from sight blocking. A target figure can still obscure a farther target figure. Movement's threshold follows the blocking unit's mount status. |
| Range/cover | One quantum below/equal/above each threshold using exact imperial bands and inch distances; a base sliver outside cover denies whole-unit cover; a high-terrain tangent is governed by the documented crossing policy. |
| Charge | First mover contacts, but final figure forces whole-unit S reduction making contact impossible: restore all charging positions while retaining spent grant and reactions. |
| Exhaustion timing | Unit enters melee exhausted, enemy spends fatigue, -1 remains. Unit becomes exhausted only later in melee, no retroactive -1. |
| Equipment and close ranks | An otherwise eligible foot defender with Improvised Projectiles cannot close ranks when charged. Independently reject bows, slings, composite bows, javelins, crossbows, horse mounts, heavy weapons, and Unarmed. Test combined restrictions and an additional test-only definition carrying the prohibition to prove the list is extensible. An eligible ordinary foot defender without restricting equipment remains allowed when charged; shooting never offers the choice. Stale client intents must also be rejected. |
| Resilience threshold | With cap 3, Resilience(1) at fatigue 2 cancels one casualty and reaches fatigue 3; at fatigue 3 it cancels none. Repeated exchanges stop immediately upon reaching the cap. |
| Resilience capacity | Resilience(2) cancels either one or two casualties for one fatigue. Three casualties need two exchanges if capacity remains; at fatigue 2/cap 3 only one exchange is available, leaving at least one casualty. No fractional fatigue or exchange with zero casualties. |
| Presence scope | Identical figures count as four for an applicable SAGA ability but as one for a special rule, physical geometry, ordinary combat-pool cap, and scoring. |
| Loss accounting | A Hero facing several uncancelled casualties cannot survive by preventing only one simply because it has one physical figure. Bodyguards transfer cannot recursively bounce. |
| Melee outcome | Earlier ability losses differ from Step 6 casualties. Mutual destruction draws; solid-cover defender not outnumbered forces attacker withdrawal; no retreat when a unit is destroyed. |
| Withdrawal | Full-S route available rejects a shorter route. Blocked required retreat triggers the opposing minimum-separation fallback, without terrain/repeat fatigue. |
| Scoring | Five slain Warriors total three points, not five per-figure rounded points. Split those losses among units without changing class subtotal; add only the appropriate destruction bonuses. |
| Terminal thresholds | 7-0 and 8-7 draw; 8-6 wins. Zero generated at turn start uses a different terminal reason. Warlord death without zero generation does not automatically end play. |
| Content readiness | A valid generic roster can be previewed before all mechanics exist, but enforced start fails while Resilience, required equipment behavior, board costs, or selected scenario capabilities are missing. No incomplete rule is silently ignored. |

## Network, security, and recovery cases

- Two clients answer the same choice simultaneously; exactly one commits. Replay the winning receipt; a changed payload with the same ID is rejected.
- Re-send a command after a lost response and after a server restart; no second roll, spend, fatigue, or casualty occurs.
- Owner, opponent, spectator, and forged seat each attempt movement, ability triggering, casualty selection, and phase advance. Validate both phase and choice ownership.
- A nonactive defender resolves its legitimate combat/reaction choices; a global active-player guard must not reject it.
- Disconnect during terrain placement, Orders allocation, reaction, close ranks, effect ordering/rerolls, casualty prevention/removal, and withdrawal. Game pauses and resumes the identical choice/state.
- Crash after commit before broadcast; retry receives committed outcomes. Crash before commit does not leave partial state. Broadcast failure cannot turn a committed action into a rejection.
- Drop/duplicate/reorder incoming event delivery; client detects a domain gap, resyncs, and converges. Private HELLO/errors do not cause false gaps.
- Load a snapshot with unknown schema, rules revision, pack hash, or missing capability; reject with a recoverable diagnostic or execute a documented migration. Never silently change live rules.
- Ensure snapshots, logs, replay exports, and opponent projections exclude resume credentials and unrevealed setup drafts.
- Try legacy MOVE_TOKEN/ACTIVATE_TOKEN/ROLL_DICE/undo against enforced play. They cannot bypass costs, legal windows, terminal state, or known random outcomes.

## End-to-end acceptance scripts

Use the approved generic pack for initial complete-game runs, including its specified activation/board model. Later faction packs receive their own complete-game runs. Synthetic fixtures may exercise additional core mechanics, but cannot substitute for approved selectable content. Record versions, configuration, event export, test result, and any defects for each run.

### E01 - Full ordinary game

1. Create an enforced six-point Clash room; join two stable seats and a read-only observer.
2. Use the generic pack for both seats, legal troop purchases and base choices, the imperial band/inch measurement configuration, chaos off; accept named digital setup conventions.
3. Complete d6 first-player setup (coin toss on ties), terrain alternation/reposition/final offer, Clash's first-player total-unit declaration and deployment A with unit grouping/equipment chosen at each step, and second-player pregame dice. Verify invalid actor/zone/cost/count/remainder attempts are rejected.
4. Play Orders with carry-over allocations, both reaction windows, all applicable approved generic abilities; exercise advanced timing separately with conformance fixtures if absent from the generic board. Exercise free and paid activations, manoeuvre, rest, repeat fatigue, and optional fatigue spending.
5. Resolve at least one covered shot, reaction changing eligibility, charge, closed-ranks melee, casualty-prevention choice, unit destruction fatigue, and withdrawal. Both clients show the same rolls and outcomes.
6. Complete six turns each without an earlier defeat; compare score categories, winner/draw, final board, and completed-turn counts with independently calculated expectations.
7. Export/replay; compare canonical final hash. Attempt a post-game move/ability/end-turn and confirm rejection. Rematch creates a new game.

### E02 - Setup and source options

Run deployment B with both diagonals/edge assignments and C from both seats. Include odd first-player unit count, maximum terrain catalog counts, one-large restrictions, nonround bases, and exact imperial distances and C-to-S distance-label normalization (without changing Method C). Exercise every sourced equipment/Hero rule via the core suite and all selectable faction options via pack tests. Verify all owner rulings Q01-Q11, including corrected Q05: an Improvised Projectiles defender cannot close ranks when charged. Exercise each equipment/status prohibition independently and in combination, plus a legal ordinary foot defender as a positive control.

### E03 - Scenario endings and chaos

Cover normal victory, score draw, turn-start zero generation, Warlord loss without immediate defeat, and concession from each seat. For each of six chaos results, test setup application, per-player first-turn/whole-game duration, interactions with mounted terrain and repeat fatigue, and final scoring. Judgement must participate in zero-generation logic; Slaughter bonuses must apply exactly once.

### E04 - Interrupted game

During a real E01 session, refresh one browser at an opponent choice, disconnect both players, and restart the server at a persisted combat checkpoint. Rejoin the original seats, preserve pending decisions and dice, finish the game, and compare against uninterrupted scripted replay. Attempt to join as a different seat using only a public room ID and verify it cannot claim an existing army.

### E05 - Pack completeness

For every ability on each supported board, demonstrate a legal trigger and an illegal timing/cost/target case, plus declared interactions/expiry and relevant cancellation cases. Run a full generic-versus-generic game with different legal loadouts and swap the warbands between seats; later faction packs also require swapped-seat runs. Confirm no unsupported list options or synthetic fixtures are selectable and every required effect has a working UI choice.

## Repository checks during implementation

When schema changes, regenerate from repository root:

```sh
python3 tools/generate_types.py
pnpm --dir apps/web generate-types
```

Run the applicable API checks with working directory `services/api`:

```sh
poetry run ruff check .
poetry run mypy app
poetry run pytest -q
```

Run web checks from repository root:

```sh
pnpm lint:web
pnpm build:web
```

Add the selected web unit/browser test commands to package scripts and CI when those suites are introduced. The web build currently regenerates TypeScript; verify generated output is consistent with the schema. Run narrow tests during development and the required full checks for the completed slice. Broaden/repeat only after changes or unresolved failures justify it.

For this documentation-only plan, appropriate validation is local link/ID/dependency checks, source-page/table review, `git diff --check`, and verification that no code, schema, PDF, OCR, or unrelated files enter the commit. Runtime test execution would not establish whether this plan is complete.

## Release checklist

- [ ] R01-R34 map to implemented paths and meaningful passing tests; core source questions resolved or explicitly named agreed variants, with no concealed approximations.
- [ ] The four generic base profiles, inherited rules, seven derived loadouts, and approved generic activation/board model are versioned and verified for both seats. Later selectable faction packs require complete sourced lists/boards; they are not prerequisites for the initial generic implementation.
- [ ] All three deployment methods, seven terrain presets, six optional chaos effects, equipment/Hero rules, scoring paths, and digital conventions are covered.
- [ ] Two people can complete the game through UI only; no manual dice, score edits, hidden debug command, or unimplemented choice remains.
- [ ] Reconnect, both-player disconnect, process restart, dedupe, and storage restoration pass; no committed state lost.
- [ ] Replay and snapshot-plus-tail reproduce both clients' terminal state and score from pinned versions.
- [ ] Existing sandbox regression checks and new enforced-game API/web/browser checks pass in CI.
- [ ] Current protocol/data model, source/coverage registry, context snapshot, next tasks, and risks match shipped behavior.
