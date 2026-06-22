# Data Model (Draft)

The MVP uses in-memory state. Later, persist snapshots + event logs.

## Coordinate system
Use **continuous coordinates** in millimeters (mm) to avoid floating conversion errors.

- Table origin: top-left (0,0)
- +x to the right, +y downward
- Facing angle in degrees (0 = right, 90 = down) or radians (pick one and stick to it)

## Entities

### Game
- id
- created_at
- rules_module
- players[]
- phase (lobby / running / finished)
- active_player_id
- round
- state_version

### RulesModule
- id
- name
- version
- unit_types[]
- terrain_traits[]
- ability_timings[]
- scenarios[]

### RulesModule.unit_types[]
- id
- name
- role
- min_figures
- max_figures
- base_profile_id
- generates_saga_dice_at_figures

### RulesModule.terrain_traits[]
- id
- name
- movement_effect
- cover_effect
- blocks_line_of_sight
- adds_fatigue_on_entry

### RulesModule.ability_timings[]
- id
- name
- phase
- trigger_window
- repeatable_per_turn

### RulesModule.scenarios[]
- id
- name
- board_width_mm
- board_height_mm
- setup_steps[]
- turn_limit
- objective_ids[]

### Token
- id
- label
- x_mm
- y_mm
- r_mm
- activation_count_this_turn
- last_activation_type (`move` / `charge` / `shoot` / `rest` / null)
- tags/status (activated, fatigued, etc. — rules-specific)

### Player (ephemeral MVP presence)
- id
- label
- connected_via (websocket session, in-memory only)

### Event
- seq (monotonic)
- type
- payload
- server_time
- actor_player_id (optional)
- client_msg_id (optional echo when tied to a client command)

### Connectivity payloads
- `PING.payload`: `{ client_time?: string }`
- `PONG.payload`: `{ echo: { client_time?: string } }`

### Presence payloads
- `HELLO.payload.players`: `Player[]`
- `HELLO.payload.self_player_id`: `string`
- `HELLO.payload.rules_module`: `RulesModule`
- `HELLO.payload.turn`: `{ phase, round, active_player_id }`
- `HELLO.payload.initiative`: `Initiative | null`
- `HELLO.payload.undo`: `UndoState`
- `PLAYER_JOINED.payload.player`: `Player`
- `PLAYER_LEFT.payload.player_id`: `string`

### Turn payloads
- `INITIATIVE_ROLLED.payload.initiative`: `Initiative`
- `TURN_ORDER_CHOSEN.payload.initiative`: `Initiative`
- `INITIATIVE_RESET.payload.reason`: `string`
- `GAME_STARTED.payload.turn`: `{ phase, round, active_player_id }`
- `TURN_CHANGED.payload.turn`: `{ phase, round, active_player_id }`
- `GAME_STARTED.payload.undo`: `UndoState`
- `TURN_CHANGED.payload.undo`: `UndoState`

### Initiative payload (`Initiative`)
- winner_player_id
- loser_player_id
- winner_roll
- loser_roll
- chooser_choice (`FIRST` | `SECOND` | `null`)
- first_player_id (`string` | `null`)
- second_player_id (`string` | `null`)

### Dice roll payload (`DICE_ROLLED`)
- count
- sides
- modifier
- rolls[]
- total
- notation

### Undo payloads
- `UNDO_REQUESTED.payload.request`: `UndoRequest`
- `UNDO_REQUESTED.payload.undo`: `UndoState`
- `UNDO_APPLIED.payload.request`: `UndoRequest`
- `UNDO_APPLIED.payload.token`: `Token`
- `UNDO_APPLIED.payload.undo`: `UndoState`
- `UNDO_REJECTED.payload.request`: `UndoRequest`
- `UNDO_REJECTED.payload.undo`: `UndoState`
- `UNDO_CANCELLED.payload.reason`: `string`
- `UNDO_CANCELLED.payload.undo`: `UndoState`

### Undo request (`UndoRequest`)
- requester_player_id
- responder_player_id
- action_type (`MOVE_TOKEN` | `ACTIVATE_TOKEN`)
- token_id

### Undo state (`UndoState`)
- pending_request (`UndoRequest` | `null`)
- undo_used_this_turn_player_ids (`string[]`)

## Geometry checks (server-side)
- token collision rules (depends on game system; start permissive)
- movement distance constraints
- line-of-sight helpers (later)
