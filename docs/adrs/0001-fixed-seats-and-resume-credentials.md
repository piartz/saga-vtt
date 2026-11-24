# ADR 0001: Fixed player seats, resume credentials, and pause on disconnect

## Status
Accepted (2026-11-24). Records decisions D01 and D06. Implemented in P01.2; durable resume in P14.2. Requirements: R27, R30.

## Context
Today every websocket gets a new ephemeral player identity. Turn order follows the connection list, and a disconnecting active player has their turn passed automatically. A SAGA game needs ownership that survives reconnects: units, dice, fatigue, and pending choices belong to a player, and the non-active player owns reaction, close-ranks, and casualty decisions. Connection order cannot grant authority, and a dropped socket cannot be allowed to skip an opponent's decision or forfeit a game.

## Decision
- An enforced game has exactly two **seats** with stable seat IDs. Seat order and turn order are fixed by game configuration and the scenario's first-player procedure, never by connection order.
- A client claims a free seat and receives a private, randomly generated **resume credential** (at least 256 bits). The server stores only a hash and compares it in constant time. The client presents it in its first websocket message, never in the URL, so it stays out of access logs. Credentials never appear in snapshots, events, logs, replays, or opponent projections.
- **Presence** (connected sockets) is separate from identity. Multiple sockets for one seat share that seat's permissions and cannot create extra turns or choices. Additional clients are read-only **spectators** and cannot issue gameplay commands.
- When a seat disconnects, an enforced game is **paused**: the exact phase, resolution stack, and pending choices are kept. Pause and resume are gameplay transitions that advance the state version. There is no implicit auto-pass, forfeit, or deadline in casual play; timed modes need an explicit pregame policy and are out of scope.
- A game survives with zero connections, under a configurable retention policy. Losing the last socket no longer deletes an enforced room.
- Full user accounts are not required for this milestone.

## Consequences
- Reconnect restores the same seat, ownership, and pending choice. An opponent's decision can no longer be erased by disconnecting.
- Authorization checks move from "is the active player" to "owns this seat and this choice". The current blanket active-player guard must not reject a legitimate defender choice (P05).
- Sandbox rooms may keep ephemeral identities and today's behavior (see ADR 0003).
- A lost credential cannot be recovered without accounts; acceptable for casual two-player play.
- Durable storage of seats and credential hashes waits on the P14 store (ADR 0002). Before then, a server restart still loses games.
