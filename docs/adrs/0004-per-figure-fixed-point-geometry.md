# ADR 0004: Per-figure geometry with fixed-point imperial measurement

## Status
Accepted (2026-11-24). Records decisions D02, D03, and D14 and owner rulings Q01/Q03. Implemented in P03; contact and withdrawal conformance in P10. Requirements: R01, R02, R04, R05, R31. The numerical tolerance bound is deliberately left to P03.3 (see Consequences).

## Context
The bootstrap board stores one token per unit in whole millimetres on an 800 x 500 mm board. SAGA legality depends on individual bases:
- cohesion, contact, and line of sight;
- terrain overlap and the base sliver outside cover;
- casualty choice and withdrawal.

It also depends on exact band thresholds, VS/S/M/L = 2/4/6/12 inches. Whole millimetres cannot represent those exactly, and floating-point thresholds make "exactly at range" ambiguous.

## Decision
- **Individual figures are authoritative.** Each figure has a stable ID, a base shape and dimensions, and a pose. A unit is a set of figures with a derived alive count. Group movement is a UI convenience that produces per-figure routes and final poses; enforced play never uses an aggregate unit footprint.
- **Fixed-point coordinates.** Positions and lengths are integers in tenths of a millimetre (`q`; 10 q = 1 mm). One inch = 254 q exactly, so VS/S/M/L = 508/1016/1524/3048 q. The table is 48 x 36 inches and the ruler is 1 inch wide. Legacy whole-mm values convert by multiplying by ten. Coordinates are versioned once, when the protocol changes; existing integer-mm fields are not silently reinterpreted.
- **Imperial, band-first display.** Player-facing distances use bands, otherwise inches. Distance label C normalizes to S without changing other uses of C, such as deployment Method C. No metric rules mode is planned. These values are recorded in `services/api/app/rules/provenance/data/conventions.json`.
- **Exact comparisons decide thresholds** wherever feasible: integer or rational arithmetic on squared distances for circular bases and rationally placed polygons. Epsilons are not scattered through rules code, and legality is never enlarged by a client pixel or the viewport.
- **Curated shapes first.** Start with source-defined base shapes and curated terrain footprints; widen the editor only after the geometry tests pass. Artwork never affects geometry.
- Rules supply policies (e.g. movement versus sight gap thresholds; see `rules-roadmap/rules-module-design.md`). Generic geometry in `services/api/app/geometry/` supplies the queries and never branches on rule names.

## Consequences
- Range, cover, and cohesion tests can assert exact equality and one quantum either side of each threshold.
- The protocol and snapshot change shape (figures and `q` units). That is a versioned migration, and the board renders individual bases.
- **Open, owned by P03.3:** irrational cases (rotated non-round bases, oval approximations, tangents to high-terrain boundaries) need a single documented tolerance/error bound and its direction of resolution. P03.3 must amend this ADR, or add a superseding ADR, with that bound, boundary fixtures, and a deterministic contact/withdrawal feasibility method. Until then, the affected charge and withdrawal behavior cannot be claimed as enforced.
- Charge and withdrawal become constrained-placement problems. A heuristic that fails to find a route is not proof that none exists; unresolved placements stay pending for correction.
