# LLM Playbook (for code-assisting tools)

Use this file as context when you ask an LLM to help implement features.

## Project constraints
- Do not add copyrighted rule text, unit profiles, battle boards, or artwork.
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

## Near-term tasks you can ask an LLM to implement
1. **WebSocket client wrapper**
   - Create a `WsClient` class with `connect()`, `sendCommand()`, `onEvent(cb)`
   - Automatic reconnect with backoff
2. **Server connection manager**
   - Track connections per room
   - Broadcast events
   - Add basic JOIN/LEAVE and player list
3. **Move token command**
   - Add command validation
   - Use mm integer coordinates
   - Broadcast TOKEN_MOVED event
4. **Board improvements**
   - Pan/zoom
   - Drag preview + “confirm” button (don’t commit movement until server confirms)
5. **Dice roller**
   - Server-side RNG using `secrets`
   - Broadcast DICE_ROLLED with results + audit fields

## Prompt template
When asking an LLM for code, paste:
- the relevant files (or file paths)
- the exact acceptance criteria (tests + UX)
- the constraints above

Example:
“Implement MOVE_TOKEN command server-side with tests. Constraints: server-authoritative, mm ints, no rules text.”
