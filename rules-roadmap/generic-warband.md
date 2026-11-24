# Initial Generic Warband

Status: planning only. Source: project owner rulings on 2026-11-24. Implement this pack first, before selecting named factions. These are explicit generic-pack profiles; do not overwrite them with different book defaults or present the pack as an official faction.

## Selectable profiles

Notation is melee (shooting) for both Aggression and Armour. A shooting characteristic does not by itself grant a ranged weapon, range, or shooting activation.

| Profile | Aggression: melee | Aggression: shooting | Armour: melee | Armour: shooting | Ordinary ranged option |
| --- | --- | --- | --- | --- | --- |
| Warlord, foot | 8 | 4 | 5 | 5 | None; an explicit effect may enable an attack |
| Warlord, horse | 8 | 4 | 5 | 4 | None; an explicit effect may enable an attack |
| Hearthguards, foot | 2 | 1 | 5 | 5 | None; an explicit effect may enable an attack |
| Hearthguards, horse | 2 | 1 | 5 | 4 | None; an explicit effect may enable an attack |
| Warriors, foot | 1 | Not specified by owner | 4 | 4 | None |
| Levies, foot | 1/2 | 1/3 | 3 | 3 | None; an explicit effect may enable an attack |
| Levies, foot with bow | 1/2 | 1/3 | 3 | 3 | Bow, range L |

The owner explicitly confirmed Armour 3(3) for **both** Levy options. Do not apply another bow penalty to make either 2(2). Both share the stated Aggression 1/2(1/3); do not swap the fractions or inherit the book's different ranged-Levy melee profile. Mounted Warlord/Hearthguard Armour above already includes the horse adjustment; do not subtract it twice. Other applicable horse/bow rules still apply, including movement, terrain fatigue, cover and close-ranks restrictions.

The missing Warrior shooting value is not a selectable shooting capability. A future effect that uses it must supply or resolve that value before it can be enabled; never invent a value or assume melee aggression equals shooting aggression. Effects specifying their own pool need not use a unit shooting characteristic.

Keep profile provenance, explicit final-stat overrides, and ordinary equipment-derived changes separate. Core book profiles may remain in a separately identified reference pack for conformance tests; generic play always selects this pack's values. The existing core recruitment bundles, Warlord rules, unit-size rules, and SAGA-die generation thresholds remain the baseline unless a later owner ruling overrides them. No other selectable loadouts, named Heroes, mercenaries, or Legendary upgrades are part of this starter pack.

## Recruitment and deployment

Buy the warband's troop quantities within the agreed budget. Keep these as an unassigned recruitment pool until the relevant deployment opportunity. During each scenario-directed deployment step, the player chooses legal unit sizes and allowed equipment from that pool, then places those units. The opponent may react by choosing their own groupings on their deployment step; the first player may organize their remainder later. Lock each committed deployed unit, not the whole future unit organization.

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

- All seven selectable profiles match the table; prohibited mounted Warriors/Levies and extra weapons are rejected.
- Mounted Armour 5(4) is not reduced a second time; both Levy options remain 3(3).
- Five generic Levy archers contribute ceil(5/3)=2 shooting dice before bonuses; five Levies contribute ceil(5/2)=3 melee dice with or without bows.
- A foot Warlord cannot shoot merely because its profile contains shooting Aggression 4; an explicitly enabling effect uses that value as specified.
- Players commit groupings during their own scenario deployment steps, retain an unassigned pool between steps, and cannot edit previously committed opponent-visible units.
- Scenario quota policies are tested independently; no generic engine rule hardcodes the example half/all/remainder sequence.
- Fatigue cancellation consumes dice/free use, opens no Activation/Reaction window, and changes no resolved-action counter. Old Grudge cannot provide a second free attempt after cancellation.
- Both heads and tails produce the preassigned winner; no-tie d6 results require no toss; duplicate requests never toss twice.
