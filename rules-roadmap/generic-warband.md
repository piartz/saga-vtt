# Initial Generic Warband

Status: planning only. The owner selected the seven starter loadouts and, in the latest correction on 2026-11-24, directed that their characteristics and special rules come from CORE-2022 pp.44-47 and the referenced special-rule/equipment sections (pp.36-39). This supersedes the earlier owner-supplied numerical profiles, including the earlier confirmation of equal Armour for both Levy options. Implement this generic pack first; it is not an official faction.

## Base profiles and troop rules

Armour is one base characteristic. Aggression has separate melee and shooting characteristics; store fractions exactly. These definitions precede equipment, conditional troop rules, fatigue, and ability effects.

| Troop profile | Base Armour | Base melee Aggression | Base shooting Aggression | SAGA dice per surviving on-table unit | Inherent rules |
| --- | --- | --- | --- | --- | --- |
| Warlord (Hero) | 5 | 8 | 4 | 1 | Determination, We Obey, Presence, Bodyguards, Pride, Resilience(1) |
| Hearthguards | 5 | 2 | 1 | 1 | No additional profile special rules |
| Warriors | 4 | 1 | 1/2 | 1 if at least 4 figures remain; otherwise 0 | Generation threshold |
| Levies | 4 | 1/3 | 1/2 | 1 if at least 6 figures remain; otherwise 0 | Generation threshold; melee Aggression becomes 1/2 when equipped without ranged weapons |

A shooting characteristic does not by itself grant a ranged weapon, range, or shooting activation. Keep the characteristic even when the loadout has no ordinary shooting option, for an explicitly enabling effect that uses it. Ordinary weapons need no special equipment tag; absence of ranged weapons does not confer the **Unarmed** special rule.

Both Warlord loadouts inherit all six rules below. See [R21](rules-coverage.md#r21---core-hero-rules) for interaction cases and P11 for implementation. Hero classification does not itself grant the separate Heroic Unit rule or accompanying figures.

| Warlord rule | Required behavior |
| --- | --- |
| Determination | One free activation of any type in its owner's Activation phase; ordinary legality still applies. A cancelled attempt consumes the grant. |
| We Obey | Once in its owner's Activation phase, grant a friendly unit within S one free activation of any type. An exhausted provider cannot use this rule. |
| Presence | Count the figure as four only for applicable SAGA ability effects/targets (Q04); all other counts remain physical. |
| Bodyguards | Prevent a pending casualty by removing an eligible friendly Hearthguard within S. That removal cannot be cancelled while retaining the prevention, or redirected again. It does not count toward melee outcome or the specified advanced-ability casualty conditions. |
| Pride | An enemy Hero within charge reach restricts the Warlord's charge target to an eligible enemy Hero; if several qualify, its owner chooses. |
| Resilience(1) | Exchange one fatigue for one pending casualty while below exhaustion, rechecking before each exchange. Reaching the cap is allowed under Q02. Compose with Bodyguards without discarding excess pending casualties merely because the Warlord is one figure. |

## Selectable loadouts and derived characteristics

The following is a derived preview before fatigue or ability effects, not seven independent base profiles. A later Armour display such as 5(4) is shorthand for the resolved melee/shooting values. Apply each equipment modifier once to the shared base profile and retain its source in the breakdown.

| Loadout | Melee Aggression | Shooting Aggression | Derived melee Armour | Derived shooting Armour | Ordinary ranged option |
| --- | --- | --- | --- | --- | --- |
| Warlord, foot | 8 | 4 | 5 | 5 | None |
| Warlord, horse | 8 | 4 | 5 | 4 | None |
| Hearthguards, foot | 2 | 1 | 5 | 5 | None |
| Hearthguards, horse | 2 | 1 | 5 | 4 | None |
| Warriors, foot | 1 | 1/2 | 4 | 4 | None |
| Levies, foot without ranged weapons | 1/2 | 1/2 | 4 | 4 | None |
| Levies, foot with bow | 1/3 | 1/2 | 3 | 3 | Bow, range L |

- **Mounted / Mounts: Horses (p.39):** subtract one from shooting Armour; open-terrain move/charge is L, with M+M bending allowed only for movement. Uneven/dangerous terrain restricts movement/charge to S. Use formation radius M; deny cover and close ranks. Finishing a move/charge in uneven terrain adds one horse fatigue; dangerous terrain adds its separate fatigue too, subject to the cap and other applicable fatigue. The generic pack has no exception to these restrictions.
- **Bows and Slings (p.37), bow option only:** foot only, shooting range L, subtract one from Armour against both melee and shooting, and deny close ranks. Bow-equipped Levies use base melee Aggression 1/3; the no-ranged-weapon exception does not apply. Unequipped foot Levies retain Armour 4 and use melee Aggression 1/2.

Register inherited troop rules and equipment policies in P02, and implement their full behavior in the packages assigned by R02/R21-R23. Changing a deployment draft's loadout recomputes from the unchanged base definition; never subtract modifiers from an already derived result. No other selectable loadouts, named Heroes, mercenaries, or Legendary upgrades belong to this starter pack. Their core extension rules remain covered by R24.

## Recruitment and deployment

Use the recruitment rules on pp.44-47: an agreed 4..8 points (default 6), exactly one free Warlord, and one point per 4 Hearthguards / 8 Warriors / 12 Levies. Before forming units, allow at most one exchange of 2 Hearthguards, 4 Warriors, or 6 Levies for either other half-bundle. Ordinary deployed units contain 4..12 figures of the same troop type and equipment; the Warlord is a single-figure unit. Later casualties can reduce units below recruitment minimums.

Keep recruited figures as an unassigned pool until the relevant deployment opportunity. During each scenario-directed deployment step, the player chooses legal unit sizes and allowed equipment from that pool, then places those units. The opponent may react by choosing their own groupings on their deployment step; the first player may organize their remainder later. Lock each committed deployed unit, not the whole future unit organization.

The scenario supplies deployment order, quota basis/calculation, mandatory units, zones, and completion conditions. Do not impose a global half-army formula, require the final number of units in advance, or replace a scenario's units-based quota with points/figures. In particular, the example first-half/opponent-all/first-remainder order is not universal. Read and implement the selected scenario's exact instructions in its adapter. Check that each committed deployment leaves the remaining recruitment pool legally groupable under that scenario; no figures may be duplicated, lost, or retroactively taken from deployed units.

## Cancellation and free grants

For the clarified pre-action cancellation timing:

1. Validate the attempt and commit its paid dice or free-grant use.
2. Offer the applicable opponent fatigue-cancellation decision.
3. If cancelled, retain the cost/grant consumption, record cancellation, and do not open an Activation/Reaction opportunity for that attempted activation. Do not increment resolved activation counts or add repetition fatigue.
4. Otherwise continue to the eligible Activation/Reaction window and then action resolution. A reaction that later invalidates an action is still a separate recorded event, not grounds to erase that reaction.

The same consumption rule applies to Old Grudge: a cancelled free first attempt uses up that free opportunity even though it does not count as a resolved activation. Keep grant-use history distinct from resolved-action history so the next paid activation can still be the first resolved one.

## Initiative tie-break

Retain Clash's initial opposed d6 procedure. On a tie, resolve one server-side fair heads/tails toss instead of rerolling d6. Bind heads to the first stable seat and tails to the other before drawing, show the assignment, and record the result and winning seat. This replaces only the tie-break, not every scenario's initiative procedure. Retries/reconnects replay the same toss; clients cannot submit its result or change the assignment afterward.

## Remaining content needed for a complete generic game

This profile pack is enough to begin roster, deployment, movement, combat, and special-rule implementation. It does not define a generic battle board, symbol costs, or the full activation economy. Specify that shared generic board/cost model before claiming a complete Orders-to-result generic game. Do not silently replace SAGA dice with unlimited free activations or label synthetic test abilities as approved gameplay content. Named faction sources are a later expansion dependency, not a blocker for starting this generic pack.

## Acceptance cases

- All four base profiles and seven derived loadouts match their respective tables; prohibited mounted Warriors/Levies and extra weapons are rejected.
- Base Armour remains 5 for Warlord/Hearthguards and 4 for Warriors/Levies. Horses derive 5 melee / 4 shooting; foot Levies without ranged weapons derive 4 / 4 and bow Levies 3 / 3. Repeated queries and deployment draft changes cannot apply penalties twice or mutate the base profile.
- Five bow Levies contribute ceil(5/2)=3 shooting dice and ceil(5/3)=2 melee dice before bonuses; five Levies without ranged weapons contribute ceil(5/2)=3 melee dice. A specifically enabled Warrior shooting attack uses Aggression 1/2 unless that effect specifies its own pool.
- Both Warlord loadouts inherit all six named special rules; verify their grants, range/target restrictions, fatigue conditions, casualty interactions, and Q02/Q04 scope. Mounting neither removes a Warlord rule nor grants Heroic Unit.
- A surviving Hearthguard generates one die; Warriors at 3/4 figures generate 0/1; Levies at 5/6 generate 0/1. Equipment does not change these thresholds.
- Bow Levies and mounted units cannot close ranks; otherwise eligible foot units without restricting equipment can close ranks when charged. Mounted units receive no cover and apply both horse and dangerous-terrain fatigue when appropriate.
- A foot Warlord cannot shoot merely because its profile contains shooting Aggression 4; an explicitly enabling effect uses that value as specified.
- Players commit groupings during their own scenario deployment steps, retain an unassigned pool between steps, and cannot edit previously committed opponent-visible units.
- Scenario quota policies are tested independently; no generic engine rule hardcodes the example half/all/remainder sequence.
- Fatigue cancellation consumes dice/free use, opens no Activation/Reaction window, and changes no resolved-action counter. Old Grudge cannot provide a second free attempt after cancellation.
- Both heads and tails produce the preassigned winner; no-tie d6 results require no toss; duplicate requests never toss twice.
