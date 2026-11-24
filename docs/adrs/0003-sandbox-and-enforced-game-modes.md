# ADR 0003: Sandbox and enforced game modes

## Status
Accepted (2026-11-24). Records decisions D07 and D12. Mode boundary introduced in P01.1; legacy commands blocked in enforced play in P01.4; safe undo revisited in P14.3. Requirements: R28, R32.

## Context
The current bootstrap tabletop is useful and has a regression suite: free token moves, generic dice, token activations, and token-only undo. None of it enforces SAGA rules. Letting those commands act on a rules-enforced game would bypass costs, geometry, reactions, and known random outcomes. Token-only undo cannot refund dice or rewind a multi-step resolution either.

## Decision
- Every room has an explicit, immutable **mode**: `sandbox` or `enforced`. Existing behavior and tests continue as `sandbox`, which is the default until enforced play exists.
- Enforced rooms route commands only through the rules runtime (ADR 0002). `MOVE_TOKEN`, `ACTIVATE_TOKEN`, `ROLL_DICE`, and the current undo commands are rejected there with a typed error. Generic rolls may remain only as clearly informational, non-gameplay messages where permitted.
- **Committed undo is disabled in enforced games.** Local preview and cancel remain. A later negotiated undo may restore only a completed deterministic checkpoint with no random disclosure, opponent choice, reaction, or downstream effect since it, recorded as a compensating event. Undo never rerolls or refunds.
- Sandbox success is never evidence of SAGA conformance. An enforced game can start only when every capability the selected pack and scenario need is enforced (ADR 0005).

## Consequences
- Migration can proceed slice by slice without breaking the playable sandbox or its tests.
- The command dispatcher needs a mode-aware routing boundary from P01.1, so later rules commands do not have to be retrofitted.
- Two code paths coexist for a while. Sandbox-only behavior must not leak into enforced state.
- Players lose committed undo in enforced games until P14.3 proves a safe variant.
