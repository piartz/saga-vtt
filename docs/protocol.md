# Protocol (Commands & Events)

This is a *starter protocol* for the bootstrap. Expand it as you build rules.

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

### Room lifecycle (later)
- `JOIN_GAME` → `PLAYER_JOINED`
- `LEAVE_GAME` → `PLAYER_LEFT`
- `START_GAME` → `GAME_STARTED`

### Board interactions (later)
- `MOVE_TOKEN` → `TOKEN_MOVED`
- `ROTATE_TOKEN` → `TOKEN_ROTATED`

### Dice (later)
- `ROLL_DICE` → `DICE_ROLLED`
  - performed on the server

## Versioning
When you introduce breaking changes:
- bump a `protocol_version` constant
- include it in the initial `HELLO` event
