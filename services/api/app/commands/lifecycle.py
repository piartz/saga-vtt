"""What happens to room state when a connection joins or leaves.

These are the bootstrap policies: a join resets a pending lobby initiative; a leave cancels an
undo request it was part of, resets the lobby initiative it was part of, and passes the turn if
the active player left. ADR 0001 replaces the leave policy with pause-and-resume for enforced
games (P01.2).
"""

from __future__ import annotations

from typing import Any

from app.commands.emit import Emit
from app.commands.sandbox import reset_token_activations, reset_undo_turn_state
from app.protocol_generated import Player as PlayerState
from app.rooms import (
    BOARD_HEIGHT_MM,
    BOARD_WIDTH_MM,
    PROTOCOL_VERSION,
    GameRoom,
    connected_player_ids,
    room_initiative_snapshot,
    room_players_snapshot,
    room_rules_module_snapshot,
    room_turn_snapshot,
    room_undo_snapshot,
    room_units_snapshot,
)


def connection_opened(room: GameRoom, player: PlayerState) -> list[Emit]:
    """Events for a newly connected player, who is already registered in the room."""
    hello = {
        "game_id": room.game_id,
        "protocol_version": PROTOCOL_VERSION,
        "board": {"width_mm": BOARD_WIDTH_MM, "height_mm": BOARD_HEIGHT_MM},
        "tokens": list(room.tokens.values()),
        "units": room_units_snapshot(room),
        "players": room_players_snapshot(room),
        "rules_module": room_rules_module_snapshot(room),
        "turn": room_turn_snapshot(room),
        "initiative": room_initiative_snapshot(room),
        "undo": room_undo_snapshot(room),
        "self_player_id": player["id"],
    }
    emits = [Emit("HELLO", hello, "sender")]
    if room.phase == "lobby" and room.initiative is not None:
        room.initiative = None
        emits.append(Emit("INITIATIVE_RESET", {"reason": "player_joined"}, "others"))
    emits.append(Emit("PLAYER_JOINED", {"player": player}, "others", player["id"]))
    return emits


def connection_closed(room: GameRoom, player: PlayerState) -> list[Emit]:
    """Events after a player's connection has been removed from the room."""
    player_id = player["id"]
    anyone_left = room.connections.has_any()
    emits: list[Emit] = []

    pending_request = room.pending_undo_request
    if pending_request is not None and player_id in (
        pending_request["requester_player_id"],
        pending_request["responder_player_id"],
    ):
        room.pending_undo_request = None
        if anyone_left:
            cancelled: dict[str, Any] = {"reason": "player_left", "undo": room_undo_snapshot(room)}
            emits.append(Emit("UNDO_CANCELLED", cancelled, "room", player_id))

    initiative = room.initiative
    if (
        room.phase == "lobby"
        and initiative is not None
        and player_id in (initiative["winner_player_id"], initiative["loser_player_id"])
    ):
        room.initiative = None
        if anyone_left:
            emits.append(Emit("INITIATIVE_RESET", {"reason": "player_left"}, "room", player_id))

    if room.phase == "running" and player_id == room.active_player_id:
        remaining_player_ids = connected_player_ids(room)
        if remaining_player_ids:
            room.active_player_id = remaining_player_ids[0]
            reset_token_activations(room)
            reset_undo_turn_state(room)
            turn_changed: dict[str, Any] = {
                "turn": room_turn_snapshot(room),
                "tokens": list(room.tokens.values()),
                "undo": room_undo_snapshot(room),
            }
            emits.append(Emit("TURN_CHANGED", turn_changed, "room", player_id))
        else:
            room.active_player_id = None
            room.phase = "lobby"
            room.round = 0
            reset_undo_turn_state(room)

    if anyone_left:
        emits.append(Emit("PLAYER_LEFT", {"player_id": player_id}, "room", player_id))
    return emits
