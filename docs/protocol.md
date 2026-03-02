# Protocol (Commands & Events)

This is the current MVP protocol implemented by the API/web app.

## Envelope (WebSocket)

### Command
```json
{
  "kind": "COMMAND",
  "type": "PING",
  "client_msg_id": "uuid",
  "payload": {}
}
```

### Event
```json
{
  "kind": "EVENT",
  "type": "PONG",
  "seq": 12,
  "server_time": "2026-02-26T12:34:56Z",
  "payload": {}
}
```

## MVP command/event types

### Connectivity
- `PING` → `PONG`

### Board interactions
- `MOVE_TOKEN` → `TOKEN_MOVED`
- Server validates:
  - payload shape and token id
  - integer mm coordinates
  - board bounds (respecting token radius)
- `TOKEN_MOVED.payload`:
  - `token`
  - `client_msg_id`

### Dice
- `ROLL_DICE` → `DICE_ROLLED`
  - server-side RNG using `secrets`
  - validated payload fields:
    - `count` integer in `[1, 20]`
    - `sides` integer in `[2, 1000]`
    - optional `modifier` integer in `[-1000, 1000]` (default `0`)
  - `DICE_ROLLED.payload`:
    - `count`
    - `sides`
    - `modifier`
    - `rolls` (array of individual die values)
    - `total` (`sum(rolls) + modifier`)
    - `notation` (for example `3d6+1`)
    - `client_msg_id`

### Room lifecycle (later)
- `JOIN_GAME` → `PLAYER_JOINED`
- `LEAVE_GAME` → `PLAYER_LEFT`
- `START_GAME` → `GAME_STARTED`

## Versioning
When you introduce breaking changes:
- bump a `protocol_version` constant
- include it in the initial `HELLO` event
