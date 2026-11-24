from __future__ import annotations

import json
import secrets
from typing import Any, Dict

from fastapi import Body, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.commands import Emit, connection_closed, connection_opened, dispatch_message
from app.rooms import (
    BOARD_HEIGHT_MM,
    BOARD_WIDTH_MM,
    PROTOCOL_VERSION,
    ROOMS,
    GameRoom,
    active_lobby_rooms_snapshot,
    create_room,
    make_event,
    room_by_creator_client_id,
    room_rules_module_snapshot,
    room_units_snapshot,
    utc_now_iso,
)
from app.rooms import validate_unit_state as validate_unit_state  # re-exported for callers
from app.rules import (
    DEFAULT_RULES_MODULE_ID,
    RulesModule,
    RulesModuleManifest,
    get_rules_module,
    list_rules_modules,
    require_rules_module,
)


def selected_rules_module_from_body(body: Any) -> RulesModule:
    if body is None:
        return require_rules_module(DEFAULT_RULES_MODULE_ID)
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="POST /games body must be an object.")

    module_id = body.get("rules_module_id", DEFAULT_RULES_MODULE_ID)
    if not isinstance(module_id, str) or not module_id.strip():
        raise HTTPException(status_code=400, detail="rules_module_id must be a non-empty string.")

    try:
        return require_rules_module(module_id.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@app.get("/rules/modules")
def rules_modules() -> Dict[str, Any]:
    return {"modules": [module.snapshot() for module in list_rules_modules()]}


@app.get("/rules/modules/{module_id}")
def rules_module_manifest(module_id: str) -> RulesModuleManifest:
    module = get_rules_module(module_id)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Unknown rules module '{module_id}'.")
    return module.manifest()


@app.post("/games")
def create_game(
    body: Dict[str, Any] | None = Body(default=None),
    x_client_id: str | None = Header(default=None),
) -> Dict[str, Any]:
    rules_module = selected_rules_module_from_body(body)
    creator_client_id = x_client_id.strip() if isinstance(x_client_id, str) and x_client_id.strip() else None
    if creator_client_id is not None:
        existing_room = room_by_creator_client_id(creator_client_id)
        if existing_room is not None:
            return {
                "game_id": existing_room.game_id,
                "protocol_version": PROTOCOL_VERSION,
                "board": {"width_mm": BOARD_WIDTH_MM, "height_mm": BOARD_HEIGHT_MM},
                "tokens": list(existing_room.tokens.values()),
                "units": room_units_snapshot(existing_room),
                "rules_module": room_rules_module_snapshot(existing_room),
                "created": False,
            }

    while True:
        game_id = secrets.token_hex(4)
        if game_id not in ROOMS:
            break

    room = create_room(game_id, creator_client_id=creator_client_id, rules_module=rules_module)
    return {
        "game_id": game_id,
        "protocol_version": PROTOCOL_VERSION,
        "board": {"width_mm": BOARD_WIDTH_MM, "height_mm": BOARD_HEIGHT_MM},
        "tokens": list(room.tokens.values()),
        "units": room_units_snapshot(room),
        "rules_module": room_rules_module_snapshot(room),
        "created": True,
    }


@app.get("/rooms")
def list_active_rooms() -> Dict[str, Any]:
    return {"rooms": active_lobby_rooms_snapshot()}


async def deliver(room: GameRoom, ws: WebSocket, emits: list[Emit]) -> None:
    """Build and send each emitted event in order, so seq follows send order."""
    for emit in emits:
        event = make_event(room, emit.event_type, emit.payload, emit.actor_player_id)
        if emit.audience == "sender":
            await ws.send_text(json.dumps(event))
        elif emit.audience == "others":
            await room.broadcast(event, exclude_ws=ws)
        else:
            await room.broadcast(event)


@app.websocket("/games/{game_id}/ws")
async def game_ws(ws: WebSocket, game_id: str) -> None:
    await ws.accept()

    room = ROOMS.get(game_id)
    if room is None:
        room = create_room(game_id)

    player = room.connections.add(ws)

    try:
        await deliver(room, ws, connection_opened(room, player))
        while True:
            message = await ws.receive_text()
            await deliver(room, ws, dispatch_message(room, player["id"], message))
    except WebSocketDisconnect:
        pass
    finally:
        disconnected_player = room.connections.remove(ws)
        if disconnected_player is not None:
            await deliver(room, ws, connection_closed(room, disconnected_player))
        # Cleanup empty room
        if not room.connections.has_any():
            ROOMS.pop(game_id, None)
