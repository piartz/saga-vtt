from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

PROTOCOL_VERSION = 1
BOARD_WIDTH_MM = 800
BOARD_HEIGHT_MM = 500


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TokenState(TypedDict):
    id: str
    label: str
    x_mm: int
    y_mm: int
    r_mm: int


class PlayerState(TypedDict):
    id: str
    label: str


def default_tokens() -> Dict[str, TokenState]:
    return {
        "A": {"id": "A", "label": "A", "x_mm": 160, "y_mm": 140, "r_mm": 22},
        "B": {"id": "B", "label": "B", "x_mm": 320, "y_mm": 260, "r_mm": 22},
    }


@dataclass
class GameRoom:
    game_id: str
    seq: int = 0
    connections: List[WebSocket] = field(default_factory=list)
    players_by_ws_id: Dict[int, PlayerState] = field(default_factory=dict)
    tokens: Dict[str, TokenState] = field(default_factory=default_tokens)

    async def broadcast(self, event: Dict[str, Any], exclude_ws: WebSocket | None = None) -> None:
        for ws in list(self.connections):
            if exclude_ws is not None and ws == exclude_ws:
                continue
            try:
                await ws.send_text(json.dumps(event))
            except WebSocketDisconnect:
                ws_id = id(ws)
                if ws in self.connections:
                    self.connections.remove(ws)
                self.players_by_ws_id.pop(ws_id, None)


# In-memory room registry (MVP only)
ROOMS: Dict[str, GameRoom] = {}


def make_event(room: GameRoom, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    room.seq += 1
    return {
        "kind": "EVENT",
        "type": event_type,
        "seq": room.seq,
        "server_time": utc_now_iso(),
        "payload": payload,
    }


def create_room(game_id: str) -> GameRoom:
    room = GameRoom(game_id=game_id)
    ROOMS[game_id] = room
    return room


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def create_player(room: GameRoom) -> PlayerState:
    while True:
        player_id = secrets.token_hex(3)
        already_used = any(player["id"] == player_id for player in room.players_by_ws_id.values())
        if not already_used:
            break
    return {"id": player_id, "label": f"Player {player_id}"}


def room_players_snapshot(room: GameRoom) -> List[PlayerState]:
    return sorted(room.players_by_ws_id.values(), key=lambda player: player["id"])


def apply_move_token(room: GameRoom, payload: Any) -> tuple[TokenState | None, str | None]:
    if not isinstance(payload, dict):
        return None, "MOVE_TOKEN payload must be an object."

    token_id = payload.get("token_id")
    x_mm = payload.get("x_mm")
    y_mm = payload.get("y_mm")

    if not isinstance(token_id, str):
        return None, "MOVE_TOKEN token_id must be a string."
    if not is_int(x_mm) or not is_int(y_mm):
        return None, "MOVE_TOKEN coordinates must be integer mm values."

    token = room.tokens.get(token_id)
    if token is None:
        return None, f"Unknown token '{token_id}'."

    radius = token["r_mm"]
    if x_mm < radius or x_mm > BOARD_WIDTH_MM - radius or y_mm < radius or y_mm > BOARD_HEIGHT_MM - radius:
        return None, "MOVE_TOKEN target is out of board bounds."

    token["x_mm"] = x_mm
    token["y_mm"] = y_mm
    return token, None


class DiceRollResult(TypedDict):
    count: int
    sides: int
    modifier: int
    rolls: List[int]
    total: int
    notation: str


def apply_roll_dice(payload: Any) -> tuple[DiceRollResult | None, str | None]:
    if not isinstance(payload, dict):
        return None, "ROLL_DICE payload must be an object."

    count = payload.get("count")
    sides = payload.get("sides")
    modifier = payload.get("modifier", 0)

    if not is_int(count) or count < 1 or count > 20:
        return None, "ROLL_DICE count must be an integer between 1 and 20."
    if not is_int(sides) or sides < 2 or sides > 1000:
        return None, "ROLL_DICE sides must be an integer between 2 and 1000."
    if not is_int(modifier) or modifier < -1000 or modifier > 1000:
        return None, "ROLL_DICE modifier must be an integer between -1000 and 1000."

    rolls = [secrets.randbelow(sides) + 1 for _ in range(count)]
    total = sum(rolls) + modifier
    notation = f"{count}d{sides}"
    if modifier > 0:
        notation += f"+{modifier}"
    elif modifier < 0:
        notation += str(modifier)

    return {
        "count": count,
        "sides": sides,
        "modifier": modifier,
        "rolls": rolls,
        "total": total,
        "notation": notation,
    }, None


app = FastAPI(title="Skirmish VTT API", version="0.1.0")

# Dev-friendly CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "time": utc_now_iso()}


@app.post("/games")
def create_game() -> Dict[str, Any]:
    while True:
        game_id = secrets.token_hex(4)
        if game_id not in ROOMS:
            break

    room = create_room(game_id)
    return {
        "game_id": game_id,
        "protocol_version": PROTOCOL_VERSION,
        "board": {"width_mm": BOARD_WIDTH_MM, "height_mm": BOARD_HEIGHT_MM},
        "tokens": list(room.tokens.values()),
    }


@app.websocket("/games/{game_id}/ws")
async def game_ws(ws: WebSocket, game_id: str) -> None:
    await ws.accept()

    room = ROOMS.get(game_id)
    if room is None:
        room = create_room(game_id)

    room.connections.append(ws)
    player = create_player(room)
    room.players_by_ws_id[id(ws)] = player

    try:
        # Initial hello event
        await ws.send_text(
            json.dumps(
                make_event(
                    room,
                    "HELLO",
                    {
                        "game_id": game_id,
                        "protocol_version": PROTOCOL_VERSION,
                        "board": {"width_mm": BOARD_WIDTH_MM, "height_mm": BOARD_HEIGHT_MM},
                        "tokens": list(room.tokens.values()),
                        "players": room_players_snapshot(room),
                    },
                )
            )
        )
        await room.broadcast(
            make_event(room, "PLAYER_JOINED", {"player": player}),
            exclude_ws=ws,
        )

        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                await ws.send_text(
                    json.dumps(make_event(room, "ERROR", {"message": "Invalid JSON"}))
                )
                continue

            if data.get("kind") != "COMMAND":
                await ws.send_text(
                    json.dumps(
                        make_event(
                            room,
                            "ERROR",
                            {"message": "Envelope kind must be COMMAND.", "received": data},
                        )
                    )
                )
                continue

            command_type = data.get("type")
            if command_type == "PING":
                await room.broadcast(
                    make_event(room, "PONG", {"echo": data.get("payload", {})})
                )
                continue

            if command_type == "MOVE_TOKEN":
                moved_token, error = apply_move_token(room, data.get("payload"))
                if error is not None:
                    await ws.send_text(json.dumps(make_event(room, "ERROR", {"message": error})))
                    continue
                await room.broadcast(
                    make_event(
                        room,
                        "TOKEN_MOVED",
                        {
                            "token": moved_token,
                            "client_msg_id": data.get("client_msg_id"),
                        },
                    )
                )
                continue

            if command_type == "ROLL_DICE":
                roll_result, error = apply_roll_dice(data.get("payload"))
                if error is not None:
                    await ws.send_text(json.dumps(make_event(room, "ERROR", {"message": error})))
                    continue
                await room.broadcast(
                    make_event(
                        room,
                        "DICE_ROLLED",
                        {
                            **roll_result,
                            "client_msg_id": data.get("client_msg_id"),
                        },
                    )
                )
                continue

            await ws.send_text(
                json.dumps(
                    make_event(
                        room,
                        "ERROR",
                        {"message": "Unknown command", "received": data},
                    )
                )
            )

    except WebSocketDisconnect:
        pass
    finally:
        # Remove connection
        disconnected_player = room.players_by_ws_id.pop(id(ws), None)
        if ws in room.connections:
            room.connections.remove(ws)
        if disconnected_player is not None and room.connections:
            await room.broadcast(
                make_event(
                    room,
                    "PLAYER_LEFT",
                    {"player_id": disconnected_player["id"]},
                )
            )
        # Cleanup empty room
        if not room.connections:
            ROOMS.pop(game_id, None)
