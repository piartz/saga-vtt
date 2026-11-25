"""Parse websocket messages and route commands to their handlers.

Handlers validate and apply a command to the room and return the events to send. They never
touch sockets, so they can be tested and reused without a transport.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.commands.emit import Emit, error
from app.commands.sandbox import (
    apply_activate_token,
    apply_choose_turn_order,
    apply_end_turn,
    apply_move_token,
    apply_request_undo,
    apply_respond_undo_request,
    apply_roll_dice,
    apply_start_game,
    ensure_command_allowed,
    ensure_undo_not_pending,
    record_undoable_action,
    reset_token_activations,
    reset_undo_turn_state,
)
from app.rooms import GameRoom, room_undo_snapshot

CommandHandler = Callable[[GameRoom, str, dict[str, Any]], list[Emit]]


def _first_error(*messages: str | None) -> str | None:
    return next((message for message in messages if message is not None), None)


def handle_ping(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    return [Emit("PONG", {"echo": data.get("payload", {})}, "room", actor)]


def handle_start_game(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    initiative, message = apply_start_game(room)
    if message is not None:
        return error(actor, message)
    return [Emit("INITIATIVE_ROLLED", {"initiative": initiative}, "room", actor)]


def handle_choose_turn_order(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    turn, initiative, message = apply_choose_turn_order(room, actor, data.get("payload"))
    if message is not None:
        return error(actor, message)
    return [
        Emit("TURN_ORDER_CHOSEN", {"initiative": initiative}, "room", actor),
        Emit("GAME_STARTED", {"turn": turn, "undo": room_undo_snapshot(room)}, "room", actor),
    ]


def handle_request_undo(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    blocked = _first_error(
        ensure_command_allowed(room, actor, "REQUEST_UNDO"),
        ensure_undo_not_pending(room, actor),
    )
    if blocked is not None:
        return error(actor, blocked)
    request, undo_snapshot, message = apply_request_undo(room, actor)
    if message is not None:
        return error(actor, message)
    return [Emit("UNDO_REQUESTED", {"request": request, "undo": undo_snapshot}, "room", actor)]


def handle_respond_undo_request(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    token, request, undo_snapshot, accepted, message = apply_respond_undo_request(
        room, actor, data.get("payload")
    )
    if message is not None:
        return error(actor, message)
    if accepted:
        payload = {"request": request, "token": token, "undo": undo_snapshot}
        return [Emit("UNDO_APPLIED", payload, "room", actor)]
    return [Emit("UNDO_REJECTED", {"request": request, "undo": undo_snapshot}, "room", actor)]


def handle_end_turn(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    blocked = ensure_undo_not_pending(room, actor)
    if blocked is not None:
        return error(actor, blocked)
    turn, message = apply_end_turn(room, actor)
    if message is not None:
        return error(actor, message)
    reset_token_activations(room)
    reset_undo_turn_state(room)
    payload = {
        "turn": turn,
        "tokens": list(room.tokens.values()),
        "undo": room_undo_snapshot(room),
    }
    return [Emit("TURN_CHANGED", payload, "room", actor)]


def handle_move_token(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    blocked = _first_error(
        ensure_undo_not_pending(room, actor),
        ensure_command_allowed(room, actor, "MOVE_TOKEN"),
    )
    if blocked is not None:
        return error(actor, blocked)
    moved_token, before_token, message = apply_move_token(room, data.get("payload"))
    if message is not None:
        return error(actor, message)
    if moved_token is not None and before_token is not None:
        record_undoable_action(room, actor, "MOVE_TOKEN", before_token, moved_token)
    payload = {"token": moved_token, "client_msg_id": data.get("client_msg_id")}
    return [Emit("TOKEN_MOVED", payload, "room", actor)]


def handle_activate_token(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    if room.phase != "running":
        return error(actor, "ACTIVATE_TOKEN is only allowed while game is running.")
    blocked = _first_error(
        ensure_undo_not_pending(room, actor),
        ensure_command_allowed(room, actor, "ACTIVATE_TOKEN"),
    )
    if blocked is not None:
        return error(actor, blocked)
    updated_token, before_token, message = apply_activate_token(room, data.get("payload"))
    if message is not None:
        return error(actor, message)
    if updated_token is not None and before_token is not None:
        record_undoable_action(room, actor, "ACTIVATE_TOKEN", before_token, updated_token)
    payload = {"token": updated_token, "client_msg_id": data.get("client_msg_id")}
    return [Emit("TOKEN_ACTIVATED", payload, "room", actor)]


def handle_roll_dice(room: GameRoom, actor: str, data: dict[str, Any]) -> list[Emit]:
    blocked = _first_error(
        ensure_undo_not_pending(room, actor),
        ensure_command_allowed(room, actor, "ROLL_DICE"),
    )
    if blocked is not None:
        return error(actor, blocked)
    roll_result, message = apply_roll_dice(data.get("payload"))
    if message is not None:
        return error(actor, message)
    if roll_result is None:
        return error(actor, "ROLL_DICE failed unexpectedly.")
    payload = {**roll_result, "client_msg_id": data.get("client_msg_id")}
    return [Emit("DICE_ROLLED", payload, "room", actor)]


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "PING": handle_ping,
    "START_GAME": handle_start_game,
    "CHOOSE_TURN_ORDER": handle_choose_turn_order,
    "REQUEST_UNDO": handle_request_undo,
    "RESPOND_UNDO_REQUEST": handle_respond_undo_request,
    "END_TURN": handle_end_turn,
    "MOVE_TOKEN": handle_move_token,
    "ACTIVATE_TOKEN": handle_activate_token,
    "ROLL_DICE": handle_roll_dice,
}


def dispatch_message(room: GameRoom, actor: str, text: str) -> list[Emit]:
    """Parse one websocket text message and return the events it produces."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return error(actor, "Invalid JSON")

    if data.get("kind") != "COMMAND":
        return error(actor, "Envelope kind must be COMMAND.", received=data)

    command_type = data.get("type")
    handler = COMMAND_HANDLERS.get(command_type) if isinstance(command_type, str) else None
    if handler is None:
        return error(actor, "Unknown command", received=data)
    return handler(room, actor, data)
