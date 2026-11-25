"""Rules for the bootstrap (sandbox) commands: validation and state changes.

Each ``apply_*`` function validates a command against the room and mutates it, returning the
values its events report or an error message. None of this is SAGA rules enforcement.
"""

from __future__ import annotations

import secrets
from typing import Any, List, TypeGuard, TypedDict, cast

from app.protocol_generated import (
    ACTIVATE_TOKENPayload,
    CHOOSE_TURN_ORDERPayload,
    MOVE_TOKENPayload,
    RESPOND_UNDO_REQUESTPayload,
    ROLL_DICEPayload,
    ActivationType,
    InitiativeState,
    Token as TokenState,
    TurnState,
    UndoActionType,
    UndoRequest as PendingUndoRequest,
    UndoState,
)
from app.rooms import (
    BOARD_HEIGHT_MM,
    BOARD_WIDTH_MM,
    GameRoom,
    UndoEntry,
    connected_player_ids,
    room_initiative_snapshot,
    room_turn_snapshot,
    room_undo_snapshot,
)


ACTIVATION_TYPES: tuple[ActivationType, ...] = ("move", "charge", "shoot", "rest")


def is_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def is_activation_type(value: Any) -> TypeGuard[ActivationType]:
    return isinstance(value, str) and value in ACTIVATION_TYPES


def copy_token_state(token: TokenState) -> TokenState:
    return {
        "id": token["id"],
        "label": token["label"],
        "x_mm": token["x_mm"],
        "y_mm": token["y_mm"],
        "r_mm": token["r_mm"],
        "activation_count_this_turn": token["activation_count_this_turn"],
        "last_activation_type": token["last_activation_type"],
    }


def reset_undo_turn_state(room: GameRoom) -> None:
    room.undo_history_this_turn = []
    room.pending_undo_request = None
    room.undo_used_this_turn_player_ids = set()


def find_single_opponent(room: GameRoom, requester_player_id: str) -> str | None:
    others = [player_id for player_id in connected_player_ids(room) if player_id != requester_player_id]
    if len(others) != 1:
        return None
    return others[0]


def record_undoable_action(
    room: GameRoom,
    actor_player_id: str,
    action_type: UndoActionType,
    before: TokenState,
    after: TokenState,
) -> None:
    room.undo_history_this_turn.append(
        {
            "action_type": action_type,
            "actor_player_id": actor_player_id,
            "token_id": after["id"],
            "before": copy_token_state(before),
            "after": copy_token_state(after),
        }
    )


def latest_undoable_action_for_player(room: GameRoom, actor_player_id: str) -> UndoEntry | None:
    for entry in reversed(room.undo_history_this_turn):
        if entry["actor_player_id"] == actor_player_id:
            return entry
    return None


def apply_request_undo(
    room: GameRoom, actor_player_id: str
) -> tuple[PendingUndoRequest | None, UndoState | None, str | None]:
    if room.phase != "running":
        return None, None, "UNDO is only available while game is running."
    if actor_player_id != room.active_player_id:
        return None, None, f"REQUEST_UNDO is only allowed for active player '{room.active_player_id}'."
    if room.pending_undo_request is not None:
        return None, None, "An undo request is already pending."
    if actor_player_id in room.undo_used_this_turn_player_ids:
        return None, None, "You already used your undo request this turn."

    undo_entry = latest_undoable_action_for_player(room, actor_player_id)
    if undo_entry is None:
        return None, None, "No board action to undo this turn."
    responder_player_id = find_single_opponent(room, actor_player_id)
    if responder_player_id is None:
        return None, None, "Undo requires exactly one connected opponent."

    room.undo_used_this_turn_player_ids.add(actor_player_id)
    room.pending_undo_request = {
        "requester_player_id": actor_player_id,
        "responder_player_id": responder_player_id,
        "action_type": undo_entry["action_type"],
        "token_id": undo_entry["token_id"],
    }
    return room.pending_undo_request, room_undo_snapshot(room), None


def apply_respond_undo_request(
    room: GameRoom, actor_player_id: str, payload: Any
) -> tuple[TokenState | None, PendingUndoRequest | None, UndoState | None, bool | None, str | None]:
    pending_request = room.pending_undo_request
    if pending_request is None:
        return None, None, None, None, "No undo request is pending."
    if actor_player_id != pending_request["responder_player_id"]:
        return None, None, None, None, "Only the opponent can accept or reject this undo request."
    if not isinstance(payload, dict):
        return None, None, None, None, "RESPOND_UNDO_REQUEST payload must be an object."
    respond_payload = cast(RESPOND_UNDO_REQUESTPayload, payload)
    if not isinstance(respond_payload.get("accept"), bool):
        return None, None, None, None, "RESPOND_UNDO_REQUEST payload.accept must be boolean."

    accept = respond_payload["accept"]
    requester_player_id = pending_request["requester_player_id"]
    undo_entry = latest_undoable_action_for_player(room, requester_player_id)
    resolved_request: PendingUndoRequest = {
        "requester_player_id": pending_request["requester_player_id"],
        "responder_player_id": pending_request["responder_player_id"],
        "action_type": pending_request["action_type"],
        "token_id": pending_request["token_id"],
    }
    room.pending_undo_request = None

    if undo_entry is None:
        return None, resolved_request, room_undo_snapshot(room), False, None
    if not accept:
        return None, resolved_request, room_undo_snapshot(room), False, None

    token_id = undo_entry["token_id"]
    token = room.tokens.get(token_id)
    if token is None:
        return None, None, None, None, f"Cannot undo action for missing token '{token_id}'."

    before = undo_entry["before"]
    token["x_mm"] = before["x_mm"]
    token["y_mm"] = before["y_mm"]
    token["activation_count_this_turn"] = before["activation_count_this_turn"]
    token["last_activation_type"] = before["last_activation_type"]

    # Remove only the last matching undoable action for that player.
    for idx in range(len(room.undo_history_this_turn) - 1, -1, -1):
        entry = room.undo_history_this_turn[idx]
        if entry["actor_player_id"] == requester_player_id:
            room.undo_history_this_turn.pop(idx)
            break

    return copy_token_state(token), resolved_request, room_undo_snapshot(room), True, None


def apply_start_game(room: GameRoom) -> tuple[InitiativeState | None, str | None]:
    if room.phase != "lobby":
        return None, "Game is already running."

    player_ids = connected_player_ids(room)
    if len(player_ids) != 2:
        return None, "START_GAME currently requires exactly 2 connected players."
    if room.initiative is not None and room.initiative["chooser_choice"] is None:
        return None, "Initiative already rolled. Winner must choose first or second."
    reset_undo_turn_state(room)

    roll_a = 0
    roll_b = 0
    while roll_a == roll_b:
        roll_a = secrets.randbelow(20) + 1
        roll_b = secrets.randbelow(20) + 1

    player_a = player_ids[0]
    player_b = player_ids[1]
    if roll_a > roll_b:
        winner_player_id = player_a
        loser_player_id = player_b
        winner_roll = roll_a
        loser_roll = roll_b
    else:
        winner_player_id = player_b
        loser_player_id = player_a
        winner_roll = roll_b
        loser_roll = roll_a

    room.initiative = {
        "winner_player_id": winner_player_id,
        "loser_player_id": loser_player_id,
        "winner_roll": winner_roll,
        "loser_roll": loser_roll,
        "chooser_choice": None,
        "first_player_id": None,
        "second_player_id": None,
    }
    return room_initiative_snapshot(room), None


def apply_choose_turn_order(
    room: GameRoom, actor_player_id: str, payload: Any
) -> tuple[TurnState | None, InitiativeState | None, str | None]:
    if room.phase != "lobby":
        return None, None, "Game is already running."
    if room.initiative is None:
        return None, None, "Initiative has not been rolled. Use START_GAME first."

    initiative = room.initiative
    if initiative["chooser_choice"] is not None:
        return None, None, "Turn order was already chosen."
    if actor_player_id != initiative["winner_player_id"]:
        return None, None, "Only initiative winner can choose first or second."
    if not isinstance(payload, dict):
        return None, None, "CHOOSE_TURN_ORDER payload must be an object."

    choose_payload = cast(CHOOSE_TURN_ORDERPayload, payload)
    choice = choose_payload.get("choice")
    if choice not in ("FIRST", "SECOND"):
        return None, None, "CHOOSE_TURN_ORDER choice must be FIRST or SECOND."

    winner_player_id = initiative["winner_player_id"]
    loser_player_id = initiative["loser_player_id"]
    if choice == "FIRST":
        first_player_id = winner_player_id
        second_player_id = loser_player_id
    else:
        first_player_id = loser_player_id
        second_player_id = winner_player_id

    initiative["chooser_choice"] = choice
    initiative["first_player_id"] = first_player_id
    initiative["second_player_id"] = second_player_id
    room.phase = "running"
    room.round = 1
    room.active_player_id = first_player_id
    reset_token_activations(room)
    reset_undo_turn_state(room)
    return room_turn_snapshot(room), room_initiative_snapshot(room), None


def apply_end_turn(room: GameRoom, actor_player_id: str) -> tuple[TurnState | None, str | None]:
    if room.phase != "running":
        return None, "Game is not running. Use START_GAME first."
    if room.active_player_id is None:
        return None, "No active player is set."
    if actor_player_id != room.active_player_id:
        return None, f"Only active player '{room.active_player_id}' can END_TURN."

    player_ids = connected_player_ids(room)
    if actor_player_id not in player_ids:
        return None, "Active player is no longer connected."
    if not player_ids:
        return None, "Cannot end turn without connected players."

    current_index = player_ids.index(actor_player_id)
    next_index = (current_index + 1) % len(player_ids)
    room.active_player_id = player_ids[next_index]
    if next_index == 0:
        room.round += 1
    return room_turn_snapshot(room), None


def ensure_command_allowed(room: GameRoom, actor_player_id: str, command_type: str) -> str | None:
    # During lobby, commands remain permissive to preserve the existing bootstrap flow.
    if room.phase != "running":
        return None
    if room.active_player_id != actor_player_id:
        return f"{command_type} is only allowed for active player '{room.active_player_id}'."
    return None


def ensure_undo_not_pending(room: GameRoom, actor_player_id: str) -> str | None:
    pending_request = room.pending_undo_request
    if pending_request is None:
        return None
    if actor_player_id == pending_request["responder_player_id"]:
        return "Undo request pending. Accept or reject it first."
    return "Undo request pending. Wait for opponent response."


def apply_move_token(room: GameRoom, payload: Any) -> tuple[TokenState | None, TokenState | None, str | None]:
    if not isinstance(payload, dict):
        return None, None, "MOVE_TOKEN payload must be an object."

    move_payload = cast(MOVE_TOKENPayload, payload)
    token_id = move_payload.get("token_id")
    x_mm = move_payload.get("x_mm")
    y_mm = move_payload.get("y_mm")

    if not isinstance(token_id, str):
        return None, None, "MOVE_TOKEN token_id must be a string."
    if not is_int(x_mm):
        return None, None, "MOVE_TOKEN coordinates must be integer mm values."
    if not is_int(y_mm):
        return None, None, "MOVE_TOKEN coordinates must be integer mm values."
    x_mm_int = x_mm
    y_mm_int = y_mm

    token = room.tokens.get(token_id)
    if token is None:
        return None, None, f"Unknown token '{token_id}'."
    before = copy_token_state(token)

    radius = token["r_mm"]
    if (
        x_mm_int < radius
        or x_mm_int > BOARD_WIDTH_MM - radius
        or y_mm_int < radius
        or y_mm_int > BOARD_HEIGHT_MM - radius
    ):
        return None, None, "MOVE_TOKEN target is out of board bounds."

    token["x_mm"] = x_mm_int
    token["y_mm"] = y_mm_int
    return token, before, None


def apply_activate_token(room: GameRoom, payload: Any) -> tuple[TokenState | None, TokenState | None, str | None]:
    if not isinstance(payload, dict):
        return None, None, "ACTIVATE_TOKEN payload must be an object."

    activate_payload = cast(ACTIVATE_TOKENPayload, payload)
    token_id = activate_payload.get("token_id")
    activation_type = activate_payload.get("activation_type")

    if not isinstance(token_id, str):
        return None, None, "ACTIVATE_TOKEN token_id must be a string."
    if not is_activation_type(activation_type):
        return None, None, "ACTIVATE_TOKEN activation_type must be one of: move, charge, shoot, rest."

    token = room.tokens.get(token_id)
    if token is None:
        return None, None, f"Unknown token '{token_id}'."
    before = copy_token_state(token)
    if activation_type == "rest" and token["activation_count_this_turn"] > 0:
        return None, None, f"Token '{token_id}' cannot activate to rest after prior activations this turn."

    token["activation_count_this_turn"] += 1
    token["last_activation_type"] = activation_type
    return token, before, None


def reset_token_activations(room: GameRoom) -> bool:
    changed = False
    for token in room.tokens.values():
        if token["activation_count_this_turn"] != 0 or token["last_activation_type"] is not None:
            token["activation_count_this_turn"] = 0
            token["last_activation_type"] = None
            changed = True
    return changed


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

    roll_payload = cast(ROLL_DICEPayload, payload)
    count = roll_payload.get("count")
    sides = roll_payload.get("sides")
    modifier = roll_payload.get("modifier", 0)

    if not is_int(count):
        return None, "ROLL_DICE count must be an integer between 1 and 20."
    if count < 1 or count > 20:
        return None, "ROLL_DICE count must be an integer between 1 and 20."

    if not is_int(sides):
        return None, "ROLL_DICE sides must be an integer between 2 and 1000."
    if sides < 2 or sides > 1000:
        return None, "ROLL_DICE sides must be an integer between 2 and 1000."

    if not is_int(modifier):
        return None, "ROLL_DICE modifier must be an integer between -1000 and 1000."
    if modifier < -1000 or modifier > 1000:
        return None, "ROLL_DICE modifier must be an integer between -1000 and 1000."
    count_int = count
    sides_int = sides
    modifier_int = modifier

    rolls = [secrets.randbelow(sides_int) + 1 for _ in range(count_int)]
    total = sum(rolls) + modifier_int
    notation = f"{count_int}d{sides_int}"
    if modifier_int > 0:
        notation += f"+{modifier_int}"
    elif modifier_int < 0:
        notation += str(modifier_int)

    return {
        "count": count_int,
        "sides": sides_int,
        "modifier": modifier_int,
        "rolls": rolls,
        "total": total,
        "notation": notation,
    }, None
