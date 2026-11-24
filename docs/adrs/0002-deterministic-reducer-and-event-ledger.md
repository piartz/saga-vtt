# ADR 0002: Deterministic reducer, serialized transactions, and an event ledger

## Status
Accepted (2026-11-24). Records decisions D08 and D09. Implemented in P01.1 (reducer and in-memory store) and P01.3 (transactions, dedupe, versions, RNG); durable store in P14.1. Requirements: R28, R29, R30, R34.

## Context
The websocket handler in `services/api/app/main.py` parses, validates, mutates room state, and broadcasts inline, and `seq` advances on private responses as well as shared events. That cannot support:
- retries without rerolling dice;
- concurrent answers to one choice;
- reconnecting mid-resolution;
- replay;
- crash recovery.

Rules resolution also pauses for opponent choices, so it cannot be an in-memory call stack waiting on a socket.

## Decision
- **Decide/reduce split.** `decide(state, command, actor)` validates an intent and returns a typed rejection or a bounded plan (facts, RNG requests, choices). `reduce(state, event)` applies facts deterministically and never reads clocks, sockets, randomness, or changed content. Saved state contains no callbacks or closures; pending work is a serializable resolution stack.
- **One writer per room.** Each command runs as a serialized transaction under a per-room lock, in this order:
  1. Authenticate the seat and validate the schema.
  2. Look up the dedupe receipt for (game, seat, `client_msg_id`) *inside* the transaction. A same-payload retry returns the original receipt before any stale-version check; the same ID with a different payload is an error.
  3. Check `expected_state_version`, permissions, choice ID/version, and phase.
  4. Resolve, draw randomness only when the rules require it, and check invariants.
  5. Atomically commit the ordered domain events, the new state/snapshot checkpoint, and the receipt.
  6. Broadcast. A failed send cannot undo a committed action or allow a retry to reroll.
- **Randomness** comes from an injectable RNG service: cryptographic in production, scripted in tests. Every roll records its purpose, per-die identity, raw values, ordered transformations, and final values. Ordinary dice, SAGA dice, and the initiative coin toss are distinct families.
- **Cursors.** A domain event cursor is separate from transport sequencing. `state_version` changes only on committed gameplay mutations (including pause/resume), never on ping, presence notices, or private errors. Snapshots carry both, so clients can detect real gaps and resync.
- **Replay** folds recorded events through a version-pinned reducer. It never calls `decide`, rerolls, reruns path search, or consults current content.
- **Storage** sits behind an event-store interface. An in-memory adapter with the same transaction contract comes first. A Postgres event/snapshot/receipt store follows before release (P14). There is one server process per room; no Redis or distributed writer is planned until a deployment needs it.

## Consequences
- Duplicate, stale, and concurrent commands become safe and testable. Replay and resync become possible.
- Every state-changing intent must carry a dedupe ID and an expected version, which changes the command envelope (protocol version bump in P01.4).
- Reducers and content must stay version-pinned, or be explicitly migrated, for saved games to remain replayable.
- Until P14, games are still lost on process restart; the in-memory store is a development substrate, not durability.
