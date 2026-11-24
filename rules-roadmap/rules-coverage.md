# Rules Coverage and Source Map

This maps mechanics to implementation responsibilities and original acceptance cases. It is not a replacement rulebook. Reopen each cited section, including diagrams and sidebars, before implementing it. All requirements below are **planned**, not implemented.

## Source baseline

| ID | Reference | Status |
| --- | --- | --- |
| CORE-2022 | Local `rules/SAGA_-_Rulebook_2022_261124_161828.pdf`, English 2022 printing, ISBN 979-10-95599-25-8 | Read for this plan; 52 PDF pages. Printed numbers match one-based PDF pages for the mechanics below. |
| CORE-2022 fingerprint | SHA-256 `67c8de47a3a0171cecd0fd655d2721bfeb6b7dcc1e4ee5f4e4bdb015cd562a3f` | Pin this revision; filename alone is insufficient. |
| OWNER-2026-11-24 | Project owner clarifications recorded in the decision register | Resolves Q01-Q10, including the generic starter, deployment, cancellation, and coin-toss tie-break; takes precedence over conflicting source wording for this project. |
| ERRATA | Official corrections/FAQ applicable to this printing | Not supplied or verified; see the decision register. Do not assume the PDF is the latest rules. |
| FACTION-A / FACTION-B | Two compatible, complete faction lists, battle boards, dice mappings, and applicable corrections | Missing; required only when adding these later faction packs, not to begin the generic warband. |
| EXPANSIONS | Further Universe and Book of Battles material | Missing; separate follow-on scope. |

The PDF is image-only. OCR was used for navigation; terrain, scenario, profile, and Resilience pages were also checked visually. OCR drops table cells and confuses S with other letters. The scan uses `C` on p.35; the owner has confirmed it means S wherever used as a distance (Q01). Prefer detailed chapters over the abbreviated reference sheet on PDF p.51; record conflicts rather than resolving them from memory.

For each implemented requirement, maintain its ID, source/page/section, correction/interpretation ID, implementation paths, test paths, supported content IDs, and status (`planned`, `in_progress`, `verified`, `source_blocked`). Acceptance names below describe proposed tests, not existing tests.

## Core requirements

### R01 - Measurement, arithmetic, and precedence

**Source:** pp.5, 8-9, 42. **Packages:** P00, P03, P05.

- Use VS/S/M/L = 2/4/6/12 inches, with a 48 x 36 inch table. Use bands where applicable and inches for other player-facing distances. Normalize translated distance C to S, but preserve deployment Method C. Exact internal band lengths are 50.8/101.6/152.4/304.8 mm; do not round to whole mm or expose a metric rules mode (owner rulings Q01/Q03). Source-defined base dimensions remain exact, with conversion for display.
- Support multiples and ordered sums such as `2L` and `M+S`. Equal total lengths do not imply equivalent movement paths. Ruler width is 1 inch (25.4 mm internally); see resolved Q03.
- Measure base edges. Distinguish any-part `within`, whole-footprint `entirely within`, and strictly `further than`, including terrain footprints. Measurements may be made at any time without state mutation.
- Sum rational aggression before rounding upward; round at the specified operation, including the half discarded by closing ranks. Clamp ordinary modified d6 results to 1..6 and Armour to 2..6.
- Each player may reroll a particular ordinary die once; final results stand. Track entitlement per player, not a single global rerolled flag. SAGA dice have different reroll rules and no numeric modifiers.
- Implement explicit ability overrides, prohibition over obligation, current-state evaluation, and player ordering of their simultaneous effects. Numerical maximums may be reduced; all-target effects may not be selectively reduced.

**Acceptance:** exact/below/above range; C-to-S normalization without changing Method C; band/inch display; aggregate fractions; per-player rerolls; explicit override and prohibition precedence.

### R02 - Troop profiles and individual figures

**Source:** pp.7-8, 23, 26, 44-45; cross-check p.51. **Packages:** P02, P11.

Hero is a troop class; Warlord is a Hero profile/role. **Initial implementation uses [the owner-defined generic profiles](generic-warband.md)**, which override the values below where they differ. The following table is a separate CORE-2022 reference, not the generic pack. Do not apply equipment penalties twice to the generic final stats.

CORE-2022 base values before equipment:

| Profile | Melee/shooting Armour | Melee/shooting aggression | SAGA dice contribution |
| --- | --- | --- | --- |
| Warlord | 5 / 5 | 8 / 4 | 1 while on table |
| Other Hero | Profile | Profile | Profile |
| Hearthguards | 5 / 5 | 2 / 1 | 1 per surviving on-table unit |
| Warriors | 4 / 4 | 1 / 1/2 | 1 with at least 4 remaining |
| Levies without ranged weapons | 4 / 4 | 1/2 / unavailable | 1 with at least 6 remaining |
| Levies with ranged weapons | 4 / 4 | 1/3 / 1/2 | Same threshold |

A shooting aggression value alone does not enable shooting. Track figure ID, base, position, life state, original unit, and profile; derive surviving count from figures. Units have stable ownership, equipment, fatigue, and activation histories. Initial ordinary units contain 4..12 identically typed/equipped figures; Heroes normally stand alone. Surviving units may fall below recruitment minimums. Zero survivors means destroyed. Units cannot merge/split during play without a sourced exception.

**Acceptance:** three surviving Warriors are legal; zero figures destroy once; aggression does not grant a weapon; Hero classification is distinct from Hearthguards.

### R03 - Recruitment and faction legality

**Source:** pp.7, 44-47. **Packages:** P02, P07, P12.

Support agreed 4..8 points, default 6, exactly one free Warlord, and recruitment bundles of 4 Hearthguards / 8 Warriors / 12 Levies per point. Permit at most one half-point exchange between bundles of 2/4/6 respectively; do not allow arbitrary fractional purchases. Keep recruitment totals separate from unit grouping. Form units and choose permitted equipment during each deployment opportunity from an unassigned recruitment pool; players can react to earlier placements. The scenario defines quota counting, mandatory units, and sequence. Lock each deployed unit, not the entire undeployed organization (Q09/D05). Validate all equipment, costs, upgrades, restrictions, and mandatory options against a pinned faction pack. Preserve original counts and class provenance for scoring. Test rosters are not real factions.

**Acceptance:** budget and single-exchange limits; regrouping preserves totals; invalid faction loadouts; scenario-defined quota evaluation; regrouping undeployed troops is allowed while deployed units remain committed.

### R04 - Bases, formation, and contact

**Source:** pp.8-9, 16-18, 20-21, 28, 39. **Packages:** P03, P08, P10.

- Support circular and noncircular bases, including rectangular/oval orientation. Validate p.8 bounds: foot within 30 mm square with stated 20 mm minimum, mounted within 50 mm square with 40 x 20 mm minimum, Heroes up to 60 mm square. Define shape-specific bounds explicitly.
- Vision is 360 degrees; orientation still matters to footprint geometry.
- Require a single connected VS adjacency graph, plus an eligible reference figure within S of all others (M for horse-mounted units). Separate clusters with close neighbors are invalid.
- Validate per-figure movement order against already moved figures. Ordinary movement can choose its final reference; charge fixes the first mover as reference. Apply the intermediate positioning rules too.
- Preserve cohesion through casualties and, in melee, contact when possible. A unit centroid/aggregate token cannot enforce these rules.

**Acceptance:** single Hero/survivor formation is legal; disconnected clusters rejected; reference is a figure, not centroid; mounted radius; nonround rotation; casualty removing a formation bridge rejected.

### R05 - Terrain definitions

**Source:** pp.18, 22, 25, 29, 34-35, 39, 48. **Packages:** P03, P04.

Height, difficulty, cover, and size are independent. Uneven does not imply light cover. Impassable does not imply solid cover or a height. Any-base overlap and full-unit containment are distinct.

Any figure starting, finishing, or crossing uneven/dangerous terrain restricts the whole unit's move/charge to S. Dangerous fatigue occurs on finishing the applicable move/charge, not merely entering/crossing; withdrawal is exempt. Horse terrain fatigue is a separate contribution. Generic immunity to uneven does not confer immunity to dangerous; the horse rule specifically stacks both penalties in dangerous terrain.

High terrain blocks a sight line when it crosses boundaries at two distinct points; distinguish seeing into/out of/through it. Low terrain does not block because of difficulty. Small terrain fits `(M+VS)` square; large fits `L` square with minimum width M. Small minimum width is S (4 inches), confirmed by Q01. Define a minimum-width algorithm for supported shapes, not merely bounding-box dimensions.

Clash presets, visually verified on p.48:

| ID / label | Height | Difficulty | Cover | Max count | Size |
| --- | --- | --- | --- | --- | --- |
| fields-scrubland / Fields or scrubland | Low | Uneven | Light | 2 | Small or large; max one large |
| hill / Hill | High | Open | None | 1 | Large |
| marsh-fen / Marsh or fen | Low | Dangerous | None | 2 | Small |
| rocky-ground / Rocky ground | Low | Uneven | Solid | 1 | Small |
| ruins / Ruins | High | Uneven | Solid | 1 | Small |
| steep-hill / Steep hill | High | Uneven | None | 1 | Large |
| woods / Woods | High | Uneven | Light | 3 | Small or large; max one large |

Impassable terrain is supported as geometry even though this scenario has no impassable preset. Core buildings are treated as ruins; actual building rules require Book of Battles.

**Acceptance:** independent traits; one figure slows whole unit; crossing versus finishing; horse-dangerous stacking; high boundary crossings; size/catalog limits.

### R06 - Scenario setup and terrain placement

**Source:** pp.48-49. **Packages:** P04, P07.

Configure compatible packs, budget, imperial measurement configuration, options, and opposing long edges. Roll ordinary d6; highest player starts throughout the scenario. A tie is settled by one fair server coin toss with heads/tails bound to seats before drawing (D04/Q10), not d6 rerolls or today's d20/winner-chooses flow.

First player places the first piece; then alternate with at least S separation and catalog limits. After at least three pieces, acting player may move an existing piece up to M while preserving separation; opponent may place one final piece or decline, ending terrain setup. Do not invent a six-piece cap. After setup locks, terrain can change only through a rule effect or recorded correction.

**Acceptance:** d6 and tie policy; alternation/minimum-three; reposition followed by exactly one final offer; locked terrain rejects dragging.

### R07 - Deployment and pregame

**Source:** pp.8, 18, 47-49. **Packages:** P07, P13.

- First player rolls d6 and selects -1/0/+1, clamped to 1..6. Preserve raw/modified results; 1-2/3-4/5-6 select A/B/C.
- A: whole bases between S and L from owner's long edge. B: first player chooses diagonal; each army deploys in its corresponding half, wholly between M and L from that line. C: use each player's right-hand short edge, wholly between M and L+M from it, with no figures within M of any edge. Use player-relative coordinates.
- Clash specifies a first half including Warlord, opponent deployment, then first-player remainder; apply its unit quota/rounding in the scenario adapter. Other scenarios define their own quota basis and order. Players form units during these opportunities, not before all deployment (Q09); do not replace a units quota with points/figures or impose a global organization freeze. Validate whole footprints, formation, bounds, terrain, other units, and inter-figure barriers.
- Second player rolls and allocates three SAGA dice before turn one without triggering abilities. These are part of the same eight-die inventory.
- Apply selected chaos effects at explicit pregame checkpoints, then lock setup. Provide ready controls and legal-zone overlays.

**Acceptance:** A/B/C from both edges; odd unit count; Warlord in first batch; three pregame dice cannot trigger; no start with missing figures.

### R08 - Turn lifecycle

**Source:** pp.8, 10-15, 30, 40-42, 49. **Packages:** P05, P06, P13.

Distinguish round, player turn, active seat: six turns means six each, normally twelve player turns. Orders precedes Activation; shooting/melee are nested resolutions, not global phases. Execute turn-start victory checks, reset relevant histories for both warbands, Orders/reactions, activations, end effects, expiry, and scenario checkpoints. Do not advance with pending choices, combat, or queued activations. Use locked seat order, never connection order. Retained dice and effects survive their proper boundaries; fatigue never auto-clears at end turn.

**Acceptance:** twelve-turn limit; out-of-turn reactions; no end-turn during resolution; fatigue/retained dice persist.

### R09 - SAGA dice inventory

**Source:** pp.10-13, 40, 49. **Package:** P06.

Exactly eight identified dice per player; symbols have frequencies 3 common / 2 uncommon / 1 rare, with pack-specific mapping. Separate available, rolled/inactive, allocated/active. Spent dice return to available. Count surviving on-table generators and profile/scenario exceptions. Before initial roll, allow retained allocations to be reclaimed, atomically for a multi-die cost. Roll no more than generated, available, or eight. Open first Orders/Reaction window before allocation. Extra rolls/rerolls require effects; SAGA dice ignore ordinary numeric modifier/reroll limits. Zero generated differs from zero available; only generation is used by Clash's turn-start defeat check.

**Acceptance:** thresholds 1/4/6; conservation of eight; atomic reclaim; zero available is not zero generated.

### R10 - Allocations and ability triggering

**Source:** pp.12-15, 40-42. **Packages:** P05, P06, P12.

Separate preparing an ability from paying its allocation to trigger it. Support alternative symbols and simultaneous multi-die costs without partial payment. Basic abilities permit multiple allocations/triggers; advanced ones track placement and trigger limits separately, once each per player turn. Test a retained allocation triggered in Orders followed by reallocation without a second trigger that turn.

Interleave allocation and Orders effects; validate restrictions before spending. End Orders with the second reaction window, then return inactive dice to available. Prepared dice may remain. Track duration, target restrictions, source symbols, placement/use markers. The Activation keyword does not necessarily activate a unit.

**Acceptance:** alternative/two-die costs; independent placement/trigger limits; carried-over allocation; final reaction precedes cleanup.

### R11 - Timing and reactions

**Source:** pp.23, 27, 40-42. **Packages:** P05, P09, P10.

Core keywords: Orders, Orders/Reaction, Activation, Activation/Reaction, Shooting, Shooting/Reaction, Melee. Existing passive `melee-reaction` is not a core keyword here. Effects resolve in order; distinguish dependent effect chains from independent clauses and evaluate current values at triggering unless explicitly deferred.

Combat opportunities alternate from attacker; passing does not permanently withdraw, but two consecutive passes end the window. Fatigue occupies the relevant opportunity. At most one Activation/Reaction ability responds to a triggering occurrence; track trigger IDs, not a one-per-turn approximation. Complete nested reactions then revalidate/resume parent action. Simultaneous effects resolve attacker before defender, otherwise active player before opponent; each player chooses their own ordering.

**Acceptance:** pass/act/pass/pass; one reaction per trigger; nested resumption; nonretroactive values; dependent/independent clauses.

### R12 - Activation grants and cancellation

**Source:** pp.14-15, 21-23, 30-32, 41. **Packages:** P05, P08.

Actions require a validated grant from an ability, special rule, manoeuvre, equipment, or scenario. Implement move/charge/shoot/rest and typed scenario extensions. Free cost is independent from fatigue exemption. Exempt activations still count for later repetition. Track all resolved activations, resolved move/charge/shoot count, last resolved kind, and one-use grants separately.

Multi-unit abilities select distinct targets up front, then fully resolve each activation/combat; choose action/target at that unit's activation where allowed. Cancellation spends dice/grant but does not count as resolved or add repetition fatigue. Offer applicable fatigue cancellation before opening Activation/Reaction; a cancelled attempt opens no such window (Q07). A consumed free attempt, including Old Grudge, is not available again just because the action never resolved (Q08). Failed charges restore positions without refunding resolved reactions/costs.

**Acceptance:** no grant/no action; free versus exempt; cancellation cost/history; multi-unit queue revalidates next unit.

### R13 - Fatigue, exhaustion, and rest

**Source:** pp.28, 30-32, 35-39. **Packages:** P08-P11.

- Default exhaustion threshold/cap three; ignore extra gains. Exhausted units can only activate to rest. Profiles may override threshold.
- Every resolved move/charge/shoot after the first of those kinds in the same player turn adds fatigue. Rest then first move does not cause repeat fatigue. Count activations during the opponent's turn too.
- Repeat fatigue occurs after movement, before melee for charges, after shooting. Terrain and combat-end fatigue have separate checkpoints.
- Rest removes one fatigue and must be the first resolved activation that player turn. No second rest. Direct removal is not a rest activation.
- Unit destruction immediately gives friendly units within S fatigue, measured from the entire simultaneous pre-removal footprint; apply once per destroyed unit.
- Opponent can spend two fatigue before resolution to cancel any activation, or one to reduce move/charge to S. Only defender spends shooter's fatigue for +1 Armour. In melee either side may increase own or reduce opposing Armour, one use per opportunity, within bounds.
- Capture exhausted-at-melee-start for -1 attack results. Later fatigue changes do not retroactively change that penalty.

**Acceptance:** rest then first move; cancelled rest; destruction radius; charge fatigue before melee; latched exhaustion.

### R14 - Movement and manoeuvres

**Source:** pp.16-19, 32, 39. **Packages:** P03, P04, P08.

Default M, horse open movement L. Validate ordered per-figure routes and swept base corridors. Ordinary L can bend M+M; every nonfinal ruler must be completed. Own figures may be crossed; other-unit bases block. Gaps between figures of another unit block movement if separation <= S (M for mounted). No ending in contact with another friendly unit or ordinary movement contacting enemies.

Nonround bases reorient only at end and no base part may exceed allowed travel. Validate route, rotation, bounds, formation, and terrain atomically. Manoeuvre is a free first activation wholly on open ground and strictly further than L from every enemy throughout its path, not just endpoints.

**Acceptance:** no tunneling; L bend; full first ruler; unit-gap barriers; manoeuvre path proximity.

### R15 - Charges

**Source:** pp.20-21, 32, 36, 39. **Packages:** P08, P10, P11.

Declare exactly one reachable enemy unit and enforce Pride. Move and charge ranges are distinct. Resolve fatigue cancellation first; only if not cancelled open eligible Activation/Reaction windows, then revalidate. First mover fixes reference and must contact target; all charge rulers are collinear. Subsequent figures must contact if possible, otherwise approach as far as legally possible with ordered cohesion/radius. Never contact another enemy unit.

If the full formation cannot be placed legally, cancel and restore positions. On success, apply charge/terrain fatigue and immediately enter melee. Server must validate mandatory contact/maximal approach; client claims of impossibility are insufficient. See design for solver policy.

**Acceptance:** one target; reactions invalidate charge; contact obligation; late placement failure restores formation; immediate melee.

### R16 - Shooting eligibility and sight

**Source:** pp.22-25, 34, 37-39. **Packages:** P03, P04, P09.

Select one target; no splitting. Determine range and clear base-to-target sight per firing figure; recompute after reactions and cancel if none can shoot. Own shooters do not block; other figures and third-party unit gaps do. Do not reuse movement's gap threshold without checking p.22's distinct sight rule. Include high-terrain boundaries, multiple pieces, target figures, and 360-degree sight. Unitless shooting is a typed source with source-defined target/pool, not a fake token.

**Acceptance:** per-figure eligibility; last shooter invalidated; own versus third-unit obstruction; unitless origin.

### R17 - Shooting pipeline

**Source:** pp.23-25, 32. **Package:** P09.

Sequence: pool -> alternating abilities/fatigue -> attack rolls/effects -> defence rolls/effects -> prevention/casualties.

Initial pool = ceil(sum eligible aggression), then pre-pool bonuses limited by both natural dice and actual unit size, then cap eight; save this starting pool. Presence does not alter caps. Later bonuses are limited to twice the starting pool when rolling, normally sixteen. Implement explicit unitless exceptions; no unrestricted extra ability dice for those attacks.

Compare final results with shooting Armour, add automatic hits, grant defender hit-count dice plus bonuses. Save on 4+, or 3+ in cover; solid cover also gives +1 shooting Armour within cap. Attacker's roll effects precede defender's; each orders their own. Reroll abilities must be triggered before results are known. Defender chooses losses, including figures outside range/sight, preserving cohesion; apply prevention first and repeat-shooting fatigue afterward.

**Acceptance:** stage-specific caps; automatic hits permit defence; entire-base cover; losses outside sight; no late reroll purchase.

### R18 - Melee pipeline

**Source:** pp.26-29, 32. **Package:** P10.

Sequence: close ranks -> both pools -> abilities/fatigue -> both attacks -> both defences -> prevention/casualties -> outcome/fatigue/withdrawal.

All figures fight, not only those touching. Apply limited pre-pool bonuses, discard ceil(half) if closing ranks, then cap starting pool at sixteen. Later dice cap twice that pool, normally thirty-two; today's generic twenty-die limit is unsuitable. Close ranks is a defender choice at the melee step after a charge, subject to equipment; it is never available against shooting (owner ruling Q05). Attacker never benefits from melee cover. Save 5+, defender solid cover/closed ranks 4+.

Both pools survive simultaneous damage resolution. Defender removes first; preserve cohesion/contact, including earlier ability losses. Determine outcome using actual Step 6 losses, excluding prevented losses and Bodyguards transfers; annihilation overrides casualty comparison, mutual annihilation draws. Early destruction still permits remaining steps; contact broken before Step 4 is a distinct early ending. Combat roles are independent of active seat.

**Acceptance:** all figures participate; odd closed-ranks pool; 32 dice; simultaneous kills; early losses excluded from outcome; contact break differs from destruction.

### R19 - Withdrawal

**Source:** pp.28-29, 35. **Package:** P10.

Apply combat fatigue attacker then defender, capped. No withdrawal if either unit is eliminated. Normally loser withdraws; draw sends attacker back. Surviving solid-cover defender forces attacker back if not outnumbered, overriding normal outcome.

First withdrawing figure is furthest from enemy unit and goes S directly away from its nearest enemy. Shorter/other-direction routes require obstruction/bounds; then move remaining figures with distance/cohesion requirements. Withdrawal is not an activation or ordinary move for terrain penalties, but still respects impassable objects and contact restrictions. If the obligated unit cannot withdraw, opponent makes minimum separation. Validate necessity; do not teleport/delete figures.

**Acceptance:** draw/cover priorities; full S unless blocked; opponent fallback; no activation/terrain fatigue.

### R20 - Casualty and destruction ledger

**Source:** pp.8, 25, 28-30, 36-37, 49. **Packages:** P02, P09-P11, P13.

Separate hits, uncancelled hits, prevented/redirected casualties, actual losses, destroyed units. Do not truncate a Hero's incoming losses to one before prevention. Record figure/profile/original unit, cause, combat step, redirected status, and pre-removal position. Scoring/fatigue consume ledger facts once. Affected player owns validated casualty choices. Preserve original size independently of survivors.

**Acceptance:** Hero must prevent all lethal losses; destruction once; retry-safe choices; original size immutable.

### R21 - Core Hero rules

**Source:** pp.36-37, 44. **Package:** P11.

- Determination: one free activation in owner's Activation phase; cancellation consumes use.
- We Obey: once in owner's Activation phase, grant friendly unit within S a free activation; exhausted provider cannot use it.
- Presence: effective count four only for applicable SAGA ability effects/targets. It has no effect on special rules or other counts, including geometry, ordinary pool caps, recruitment, and scoring (owner ruling Q04).
- Resilience(X): while fatigue is below the receiving unit's exhaustion threshold, exchange one fatigue for cancellation of 1..X pending casualties. The exchange may bring fatigue exactly to the threshold. Recheck exhaustion before each further exchange; no exchanges at/above the threshold and no zero-casualty exchanges. Cancelling only one casualty with Resilience(2) still costs one full fatigue. Compose with Bodyguards without recursive redirection (owner ruling Q02).
- Bodyguards: remove eligible friendly Hearthguard within S, no recursive transfers or cancelling transferred casualty while keeping benefit; excluded from melee outcome and specified advanced-ability casualty conditions.
- Pride: reachable enemy Hero constrains charge targets. Heroic Unit uses Hero rules/dice, keeps Hero last through legal swapping, forbids leaving, and only enables Bodyguards after escorts are gone.

**Acceptance:** cancelled Determination; exhausted We Obey; Presence affects SAGA abilities but not special rules; Resilience(1) at fatigue 2 reaches cap 3; no exchange at cap; Resilience(2) cancels one or two for one fatigue; sequential exchange rechecks; Resilience/Bodyguards composition; heroic last-figure swap; reachable Hero priority.

### R22 - Ranged equipment

**Source:** pp.37, 39. **Packages:** P02, P09, P11.

These are core equipment policies. Explicit final-stat overrides in the generic pack take precedence: its bow Levies remain Armour 3(3) and Aggression 1/2(1/3). Do not apply another bow penalty to the specified final values.

| Equipment | Implementation obligations |
| --- | --- |
| Bows/slings | L, foot only, -1 both Armours, no close ranks. |
| Composite bows | M, mounted only, -1 melee Armour, no close ranks; owner's-phase free shooting, all shooting activations exempt from repetition fatigue, no consecutive resolved shooting activations. |
| Crossbows | L, foot only, -1 both Armours, +1 shooting attack results, no close ranks, no consecutive resolved shooting activations. |
| Javelins | M, -1 melee Armour, no close ranks; charging melee +1 attack results unless defender has solid cover; once per owner's Activation phase free repetition-fatigue-exempt shoot. Do not import another edition's move-triggered rule. |
| Improvised projectiles | S, target +1 shooting defence results; may close ranks when charged unless another restriction forbids it; never close ranks against shooting (owner ruling Q05). |

Another unit acting or a cancelled intervening activation does not reset consecutive-shot restrictions.

**Acceptance:** last resolved action per unit; javelin once per phase; javelin versus closed ranks; Improvised Projectiles defender can close ranks when charged; independent mounted/unarmed restriction still forbids it; no closing ranks against shooting; faction permission checks.

### R23 - Melee equipment and horses

**Source:** pp.37-39. **Packages:** P02, P08, P10, P11.

Heavy weapons: foot only, -1 melee Armour, +1 melee attack results, no close ranks. Unarmed: explicit tag, never inferred from missing equipment; opponent +1 melee defence results; no close ranks.

Horses: open move/charge L; movement may bend M+M, charge cannot; -1 shooting Armour; no cover/close ranks without explicit override; formation radius M. Ending in uneven adds horse fatigue, dangerous adds both contributions, plus applicable repetition fatigue, capped. Compose modifiers without permanently changing base stats.

**Acceptance:** horse/bow incompatibility; explicit mounted-cover override; stacked fatigue; heavy weapon/fatigue Armour bounds; unarmed is not default.

### R24 - Mercenaries, Legends, and expansion contracts

**Source:** pp.7, 44, 47. **Packages:** P02, P11-P13.

Mercenaries keep troop-class rules, fixed sourced composition/options, and cost <= half budget. Advanced board activations cannot activate them; advanced abilities in their combats are unavailable absent profile exception, but enemy fatigue can still be spent. Legendary upgrades have sourced cost/profile, one per army, both players' pregame agreement; Warlord rules persist unless overridden.

Implement core restrictions/scoring with original fixtures; do not expose invented profiles as real units. Extra types, mounts, magic, and objectives declare capabilities; reject incomplete packs rather than silently ignoring unsupported effects.

**Acceptance:** mercenary budget/composition; advanced-versus-fatigue exception; Legendary agreement/limit; unknown capabilities fail before start.

### R25 - End game and scoring

**Source:** pp.9, 49. **Package:** P13.

At player turn start, zero generated SAGA dice ends Clash in opponent's favor, after accounting for profile/scenario modifiers. Zero available is different; Warlord death alone is not defeat. Otherwise finish after six completed turns each, including pending end effects.

Score from ledger: enemy Hero 4 each, Hearthguard 1 each, Warriors half slain count, Levies one third, upward rounded at the aggregate operation. Add one per destroyed ordinary unit. Mercenaries instead add one at/below half original size or two if destroyed; Legendary destruction adds four. Do not also award ordinary unit destruction bonus to these exceptions. Specify handling if a future pack allows overlapping tags.

A winner needs at least eight points and a lead of at least two, else draw. Final facts contain reason, turns, per-category scores, and modifiers. Concession is a separate digital reason, allowed off-turn; terminal games reject gameplay mutations.

**Acceptance:** zero generation versus Warlord death; class-level rounding; exclusive unit bonuses; 7-0 draw/8-7 draw/8-6 win; finish exactly once.

### R26 - Optional battlefield chaos

**Source:** p.49. **Packages:** P07, P13.

Both players opt in before lock; roll/store one d6 result:

| Result | Required effect |
| --- | --- |
| Dawn | During each player's first turn, shooting/charge distance cannot exceed M. |
| Exhaustion | Pregame d6 per unit; 5+ adds one fatigue. |
| Cursed Ground | Convert uneven to dangerous, preserving height/cover. |
| Old Grudge | Each unit's first activation during each player's first turn is free; a cancelled free attempt consumes that entitlement even though resolved activation count stays unchanged (Q08). |
| Judgement | Each warband generates one extra SAGA die; inventory cap remains; include in zero-generation check. |
| Slaughter | Add two massacre points per entirely destroyed enemy unit. |

**Acceptance:** mutual option; all six results; per-player expiry; Judgement avoids false defeat; destruction bonus once.

## Online product requirements

These are engineering requirements, not published game rules.

| ID | Requirement | Packages | Acceptance |
| --- | --- | --- | --- |
| R27 | Stable two-player seats, private resume credentials, spectators/read-only roles, locked ownership; presence is not identity | P01, P14 | Rejoin preserves owner; third client cannot command a seat. |
| R28 | Serialized transactions, deduplication, state-version checks, typed validation, atomic rejection | P01, P05 | Duplicate cannot roll/spend twice; competing answers resolve once. |
| R29 | Audited server randomness, deterministic event reduction, versioned snapshots/content hashes | P01, P06, P14 | Replay invokes no RNG and reproduces result; retry returns original outcomes. |
| R30 | Disconnect pause, durable events/state/choices, restart recovery | P01, P14 | Recover mid-allocation/combat/casualties/withdrawal without auto-pass/new rolls. |
| R31 | Structured choices and legal actions with complete UI for both seats | P05 onward, P15 | Finish without JSON commands; opponent can act in its windows. |
| R32 | Preview/cancel; negotiated undo cannot cross random disclosure, opponent decisions, or multi-step resolutions | P01, P08, P14 | Token rollback cannot refund dice or erase known rolls. |
| R33 | Owner-defined generic pack first; approved generic board/activation content for complete play; sourced factions later | P00, P02, P12, P15 | Generic stats and all selectable loadouts match owner rulings; no invented activation costs or unsupported selectable abilities. |
| R34 | Result, score provenance, history, export/replay, full browser coverage | P13-P15 | Both clients and replay agree on final state/result. |
