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
  - `self_player_id` (the current websocket player's id)
  - `initiative` (nullable; see turn order flow below)
  - `undo` (current undo state snapshot for the running turn)
- `PLAYER_JOINED`:
  - emitted to existing room clients when a new client connects
  - payload: `player`
  - includes `actor_player_id` of the joining player
- `PLAYER_LEFT`:
  - emitted to remaining room clients when a client disconnects
  - payload: `player_id`
  - includes `actor_player_id` of the leaving player

### Turn structure
- `HELLO.payload.turn` includes:
  - `phase` (`lobby` or `running`)
  - `round` (integer, starts at `0` in lobby)
  - `active_player_id` (`string` or `null`)
- `START_GAME` → `INITIATIVE_ROLLED`
  - currently requires exactly 2 connected players
  - rolls each player's initiative (d20, re-roll ties)
  - stores initiative winner/loser and waits for winner's choice
- `CHOOSE_TURN_ORDER` → `TURN_ORDER_CHOSEN` then `GAME_STARTED`
  - payload: `{ "choice": "FIRST" | "SECOND" }`
  - only initiative winner can choose
  - `TURN_ORDER_CHOSEN.payload.initiative` includes winner choice and resulting first/second player ids
  - `GAME_STARTED.payload.turn` contains running turn snapshot after choice
- `END_TURN` → `TURN_CHANGED`
  - allowed only for the current active player
  - advances active player to the next connected player
  - increments `round` when the active player wraps to the start of the order
  - `TURN_CHANGED.payload.turn` contains the updated turn snapshot
- `INITIATIVE_RESET`
  - emitted if initiative is invalidated in lobby (for example player joins/leaves before choice)
  - payload includes `reason` (`player_joined` or `player_left`)

### Connectivity
- `PING` → `PONG`
  - `PONG` includes `actor_player_id` of the player who sent the `PING`

### Board interactions
- `MOVE_TOKEN` → `TOKEN_MOVED`
- `ACTIVATE_TOKEN` → `TOKEN_ACTIVATED`
- `REQUEST_UNDO` → `UNDO_REQUESTED`
- `RESPOND_UNDO_REQUEST` → (`UNDO_APPLIED` | `UNDO_REJECTED`)
- while `phase = running`, only active player may issue `MOVE_TOKEN`
- while `phase = running`, only active player may issue `ACTIVATE_TOKEN`
- while an undo request is pending, board/turn actions are blocked until opponent responds
- Server validates:
  - payload shape and token id
  - integer mm coordinates
  - board bounds (respecting token radius)
  - activation type (`move`, `charge`, `shoot`, `rest`)
- each `ACTIVATE_TOKEN` increments token activation count for the current turn and updates last activation type
- `ACTIVATE_TOKEN` with `activation_type = rest` is only valid when token activation count for the turn is `0`
- at each `END_TURN`, all token activations are cleared in the server state
  - `TURN_CHANGED.payload.tokens` contains the post-reset token snapshot
- `TOKEN_MOVED.payload`:
  - `token`
  - `client_msg_id`
- `TOKEN_MOVED` includes `actor_player_id` of the player who sent `MOVE_TOKEN`
- `TOKEN_ACTIVATED.payload`:
  - `token`
  - `client_msg_id`
- `TOKEN_ACTIVATED` includes `actor_player_id` of the player who sent `ACTIVATE_TOKEN`
- undo rules:
  - only board actions (`MOVE_TOKEN`, `ACTIVATE_TOKEN`) are undoable
  - undo request targets the latest undoable action made by the active player in the current turn
  - exactly one undo request is allowed per player turn
  - opponent must accept the request for state rollback to happen
  - `UNDO_REQUESTED.payload` includes:
    - `request` (`requester_player_id`, `responder_player_id`, `action_type`, `token_id`)
    - `undo` (updated undo snapshot)
  - `UNDO_APPLIED.payload` includes:
    - `request`
    - `token` (authoritative reverted token snapshot)
    - `undo` (updated undo snapshot)
  - `UNDO_REJECTED.payload` includes:
    - `request`
    - `undo` (updated undo snapshot)
  - `UNDO_CANCELLED` can be emitted if pending undo is invalidated by disconnect (`reason = player_left`)

### Dice
- `ROLL_DICE` → `DICE_ROLLED`
- while `phase = running`, only active player may issue `ROLL_DICE`
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
- explicit lobby commands (`JOIN_GAME`, `LEAVE_GAME`) once auth/identity is added

## Versioning
When you introduce breaking changes:
- bump a `protocol_version` constant
- include it in the initial `HELLO` event
