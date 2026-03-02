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
  "actor_player_id": "a1b2c3",
  "payload": {}
}
```

`actor_player_id` is optional and present when an event is attributable to a specific connected player.

## MVP command/event types

### Connection lifecycle / presence
- Server assigns an ephemeral player identity per websocket connection.
- `HELLO.payload` includes:
  - `game_id`
  - `protocol_version`
  - `board`
  - `tokens`
  - `players` (connected players snapshot)
- `PLAYER_JOINED`:
  - emitted to existing room clients when a new client connects
  - payload: `player`
  - includes `actor_player_id` of the joining player
- `PLAYER_LEFT`:
  - emitted to remaining room clients when a client disconnects
  - payload: `player_id`
  - includes `actor_player_id` of the leaving player

### Connectivity
- `PING` → `PONG`
  - `PONG` includes `actor_player_id` of the player who sent the `PING`

### Board interactions
- `MOVE_TOKEN` → `TOKEN_MOVED`
- Server validates:
  - payload shape and token id
  - integer mm coordinates
  - board bounds (respecting token radius)
- `TOKEN_MOVED.payload`:
  - `token`
  - `client_msg_id`
- `TOKEN_MOVED` includes `actor_player_id` of the player who sent `MOVE_TOKEN`

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
  - `DICE_ROLLED` includes `actor_player_id` of the player who sent `ROLL_DICE`

### Room lifecycle (later)
- explicit lobby commands (`JOIN_GAME`, `LEAVE_GAME`, `START_GAME`) once auth/identity is added

## Versioning
When you introduce breaking changes:
- bump a `protocol_version` constant
- include it in the initial `HELLO` event
