# LLM Playbook (for code-assisting tools)

Use this file as context when you ask an LLM to help implement features.

## Project constraints
- Do not add copyrighted rule prose, published examples, battle-board layout, or artwork.
- Canonical names/labels are allowed for units, terrain, special rules, battle-board abilities, scenarios, and other game terms. Implement rules behavior in code/tests without copying the source prose that explains it.
- Keep the engine generic; rules belong in a module interface.
- Server is authoritative. Clients never decide dice or final legality of actions.

## Current architecture
- Web: React + TypeScript (Vite)
- API: FastAPI + WebSocket
- Transport: JSON commands/events (see `docs/protocol.md`)
- State: in-memory (MVP); later event log + snapshots in Postgres

## Preferred patterns
- Commands are **intent**; Events are **facts**.
- The server assigns:
  - `seq` (monotonic event number)
  - `server_time`
- Each command includes `client_msg_id` for dedupe/ack later.

## Current work order

Read [project context](agent-context.md) first. The connection manager, token moves, basic dice roller, and board pan/zoom are already implemented; do not restart those bootstrap tasks.

For the game engine, follow the [implementation plan](../rules-roadmap/implementation-plan.md) and [iteration playbook](../rules-roadmap/iteration-playbook.md). Start with P00.1 for the source/requirement registry, then P01.1 for command dispatch and deterministic reduction. The [planning review](../rules-roadmap/review-readiness.md) records remaining content and engineering gates. Reconnect/recovery belongs to the P01/P14 contracts, not a separate identity system.

Current token coordinates use integer mm. Enforced-game geometry is a planned, versioned change to exact fixed-point coordinates with band/inch display; follow P03 rather than copying the bootstrap coordinate contract into new rules.

## Prompt template
When asking an LLM for code, paste:
- the relevant files (or file paths)
- the exact acceptance criteria (tests + UX)
- the constraints above

Example:
“Implement P01.1 with its listed acceptance criteria. Preserve sandbox behavior, keep rules separate from transport, and update actual code/test evidence in the requirement registry.”
