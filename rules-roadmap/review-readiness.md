# Final Planning Review

Reviewed: 2026-11-24. Scope: all roadmap documents, the supplied CORE-2022 mechanics and relevant diagrams/tables, owner rulings Q01-Q11, and current implementation evidence. This review changes documentation only.

Post-review correction on the same date: the owner relayed confirmation that Improvised Projectiles forbids close ranks. Corrected Q05 supersedes the earlier permission. Coverage, design, implementation instructions, and acceptance cases now reject it, alongside the other non-exhaustive equipment/status prohibitions.

## Readiness

The plan is ready to start P00.1 and then P01.1. No further owner rule decision blocks those slices. The generic battle board remains an explicit content gate before P12 can claim complete generic play. Geometry feasibility and numerical policy must be demonstrated in P03, with final charge/withdrawal conformance in P10. These are implementation obligations, not capabilities established by this review.

The source baseline is the supplied 2022 PDF and recorded owner rulings. Official FAQ/errata currency has not been verified; this review does not certify a later edition or expansion. Each implementation slice still reopens its source and tests the relevant behavior.

## Review coverage

| Area | Source / evidence | Result |
| --- | --- | --- |
| Measurement, fractions, bases, troop classes and formation | CORE-2022 pp.5, 7-9; owner distance rulings | Exact band/inch conversions and physical/effective counts retained; intermediate formation checks made explicit. |
| Orders, dice inventory, abilities, activation and cancellation | pp.10-15, 30-32, 40-42; Q07/Q08 | Eight-die conservation, separate placement/trigger limits, reaction priority, spent grants, and resolved-action histories remain distinct. |
| Movement, manoeuvres and charges | pp.16-21, 32, 39 | Straight/segmented routes, terrain restrictions, first-mover checks, charge contact obligations and rollback covered. |
| Shooting, melee, casualties and withdrawal | pp.22-29, 36-39 | Pool limits, sight, cover, fatigue permissions, simultaneous damage, prevention and retreat obligations checked; omissions tightened. |
| Terrain, equipment and special rules | pp.18, 34-39; Q01-Q05 | Independent terrain traits, ending-versus-crossing fatigue, every core equipment rule and Hero rule covered. |
| Recruitment, profiles and scenario | pp.44-49; corrected Q06, Q09-Q11 | Source profiles and derived equipment effects preserved; Clash now has an executable deployment-count procedure. |
| Current runtime and migration | `services/api/app/main.py`, `connections.py`, `rules/`, existing tests, schemas and generators | Passive manifests, token-only geometry, d20 initiative, ephemeral ownership and disconnect behavior remain explicitly unimplemented rules work. |
| Execution and release | P00-P15, R01-R34, validation and iteration guides | Dependencies, ownership, acceptance cases, staged content availability and recovery requirements checked. |

## Corrections made during review

- **Deployment quota:** Q11 fixes Clash's first-player total N before deployment, with ceil(N/2) including Warlord first and floor(N/2) after the opponent. Unit sizes/equipment remain flexible until committed; remaining figures must fit the remaining unit slots.
- **Intermediate formation:** ordinary movement can use an unmoved unit member for its VS neighbor check; charges and deployment require an already moved/placed neighbor. First-mover radius, final formation, and the lone-figure case have separate tests.
- **Sight gaps:** third-party unit gaps block sight without movement's S/M cutoff; firing/target-unit gaps are exempt, but intervening target figures still obstruct sight. Movement's threshold is based on the blocking unit's mount status.
- **Combat permissions and counts:** an ability prohibition also blocks combat fatigue use unless explicitly excepted; lack of allocated dice does not. Pre-pool attack bonuses are limited by natural dice and actual figure count. Bonus defence dice remain separate. Close ranks grants solid cover for withdrawal as well as saves.
- **Close-ranks equipment correction:** reject bows/slings, javelins, crossbows, horse mounts, heavy weapons, Improvised Projectiles, and Unarmed under corrected Q05; preserve composite bows and any additional sourced restrictions. Tests cover each prohibition, combinations, extensibility, and an eligible ordinary foot defender.
- **Source conflict recorded:** the p.29 melee example conflicts with the pre-pool figure-count cap stated on p.26. The plan follows the explicit p.26 rule and uses original regression arrangements. This is a recorded interpretation, not an official erratum.
- **Implementation safety:** roster previews no longer imply an enforced game is playable. All selected rules/abilities/scenario capabilities must exist before enforced start. Dedupe lookup is checked within the mutation transaction; pause/resume advances gameplay state version. Recruitment-pool figures are no longer incorrectly required to belong to a committed unit.
- **Handoff consistency:** usage limits belong to abilities rather than timing keywords; scenario count declarations occur in deployment rather than preforming the roster. The older onboarding task list now points to current slices instead of completed bootstrap work.

## Remaining gates and next steps

| Gate | Required work | Blocks |
| --- | --- | --- |
| Generic board/activation definition | Approve the complete ability list, symbol costs, target restrictions, timings, use limits and effects, including whether advanced abilities are present | P12 complete-game content; does not block P00/P01, roster or independent core mechanics |
| Geometry proof | Select supported shapes, boundary/tolerance policy and a deterministic contact/withdrawal feasibility method; validate adversarial layouts | P03 exit and P10 conformance |
| Later content | Obtain complete named faction/expansion profiles, boards and applicable corrections before enabling them | Only the added packs |
| Runtime/release evidence | Implement the planned rules, schema/UI, persistence and all acceptance checks | P01-P15 completion; documentation cannot substitute for working behavior |

Start P00.1 with the supplied source hash, requirement IDs, Q01-Q11 and the recorded source conflict. Then extract dispatch/reduction in P01.1 while preserving sandbox behavior. Keep the scope to one slice per change, and update the registry with actual implementation/test evidence.

## Documentation validation

Passed: checks across 12 Markdown files and 26 local links/anchors; fences/table widths; P00-P15 dependency order; R01-R34, D01-D15 and Q01-Q11 IDs; base/derived profile consistency; Warlord rule membership; combat-pool and Clash quota arithmetic; stale-instruction search; and `git diff --check`. Runtime tests were not run because this review changes documentation only. Implementation slices must supply the behavioral evidence described above.
