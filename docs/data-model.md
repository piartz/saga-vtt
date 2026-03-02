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
- players[]
- phase (lobby / running / finished)
- active_player_id
- round
- state_version

### Token
- id
- name
- owner_player_id
- base_diameter_mm
- position_mm: {x, y}
- facing_deg
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

### Presence payloads
- `HELLO.payload.players`: `Player[]`
- `PLAYER_JOINED.payload.player`: `Player`
- `PLAYER_LEFT.payload.player_id`: `string`

### Dice roll payload (`DICE_ROLLED`)
- count
- sides
- modifier
- rolls[]
- total
- notation

## Geometry checks (server-side)
- token collision rules (depends on game system; start permissive)
- movement distance constraints
- line-of-sight helpers (later)
