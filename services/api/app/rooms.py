"""Room state, the in-memory room registry, event construction, and state snapshots.

Shared by the HTTP endpoints, the websocket transport, and the command handlers. Rules for the
bootstrap commands live in ``app.commands.sandbox``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict

from fastapi import WebSocket

from app.connections import RoomConnectionManager
from app.protocol_generated import (
    InitiativeState,
    Phase,
    Player as PlayerState,
    Token as TokenState,
    TurnState,
    UndoActionType,
    UndoRequest as PendingUndoRequest,
    UndoState,
    Unit as UnitState,
)
from app.rules import (
    DEFAULT_RULES_MODULE_ID,
    RulesModule,
    RulesModuleSnapshot,
    require_rules_module,
)
from app.rules.types import UnitTypeDefinition


PROTOCOL_VERSION = 1
BOARD_WIDTH_MM = 800
BOARD_HEIGHT_MM = 500


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LobbyRoomState(TypedDict):
    game_id: str
    player_count: int
    phase: Phase
    round: int
    rules_module: RulesModuleSnapshot


class UndoEntry(TypedDict):
    action_type: UndoActionType
    actor_player_id: str
    token_id: str
    before: TokenState
    after: TokenState


def default_tokens() -> Dict[str, TokenState]:
    return {
        "A": {
            "id": "A",
            "label": "A",
            "x_mm": 160,
            "y_mm": 140,
            "r_mm": 22,
            "activation_count_this_turn": 0,
            "last_activation_type": None,
        },
        "B": {
            "id": "B",
            "label": "B",
            "x_mm": 320,
            "y_mm": 260,
            "r_mm": 22,
            "activation_count_this_turn": 0,
            "last_activation_type": None,
        },
    }


def unit_type_ids_by_id(rules_module: RulesModule) -> dict[str, UnitTypeDefinition]:
    return {unit_type["id"]: unit_type for unit_type in rules_module.unit_types}


def validate_unit_state(
    unit: UnitState,
    rules_module: RulesModule,
    valid_owner_player_ids: set[str] | None = None,
    valid_token_ids: set[str] | None = None,
) -> str | None:
    if not unit["id"].strip():
        return "Unit id must be a non-empty string."
    if not unit["label"].strip():
        return f"Unit '{unit['id']}' label must be a non-empty string."

    owner_player_id = unit["owner_player_id"]
    if owner_player_id is not None:
        if not owner_player_id.strip():
            return f"Unit '{unit['id']}' owner_player_id must be null or a non-empty string."
        if valid_owner_player_ids is not None and owner_player_id not in valid_owner_player_ids:
            return f"Unit '{unit['id']}' has unknown owner_player_id '{owner_player_id}'."

    unit_types_by_id = unit_type_ids_by_id(rules_module)
    unit_type = unit_types_by_id.get(unit["unit_type_id"])
    if unit_type is None:
        return f"Unit '{unit['id']}' has unknown unit_type_id '{unit['unit_type_id']}'."

    figure_count = unit["figure_count"]
    if figure_count < unit_type["min_figures"] or figure_count > unit_type["max_figures"]:
        return (
            f"Unit '{unit['id']}' figure_count must be between "
            f"{unit_type['min_figures']} and {unit_type['max_figures']}."
        )

    if unit["fatigue"] < 0:
        return f"Unit '{unit['id']}' fatigue cannot be negative."
    if unit["activation_count_this_turn"] < 0:
        return f"Unit '{unit['id']}' activation_count_this_turn cannot be negative."

    token_id = unit["token_id"]
    if token_id is not None:
        if not token_id.strip():
            return f"Unit '{unit['id']}' token_id must be null or a non-empty string."
        if valid_token_ids is not None and token_id not in valid_token_ids:
            return f"Unit '{unit['id']}' references unknown token_id '{token_id}'."

    return None


def require_valid_unit_state(
    unit: UnitState,
    rules_module: RulesModule,
    valid_owner_player_ids: set[str] | None = None,
    valid_token_ids: set[str] | None = None,
) -> None:
    error = validate_unit_state(unit, rules_module, valid_owner_player_ids, valid_token_ids)
    if error is not None:
        raise ValueError(error)


def default_units_for_rules_module(
    rules_module: RulesModule, tokens: Dict[str, TokenState]
) -> Dict[str, UnitState]:
    unit_type_ids = unit_type_ids_by_id(rules_module)
    if "warlord" not in unit_type_ids:
        raise ValueError(f"Rules module '{rules_module.id}' must define a 'warlord' unit type.")

    units: Dict[str, UnitState] = {
        "A-warlord": {
            "id": "A-warlord",
            "label": "Warlord A",
            "owner_player_id": None,
            "unit_type_id": "warlord",
            "figure_count": 1,
            "fatigue": 0,
            "activation_count_this_turn": 0,
            "token_id": "A",
        },
        "B-warlord": {
            "id": "B-warlord",
            "label": "Warlord B",
            "owner_player_id": None,
            "unit_type_id": "warlord",
            "figure_count": 1,
            "fatigue": 0,
            "activation_count_this_turn": 0,
            "token_id": "B",
        },
    }
    valid_token_ids = set(tokens)
    for unit in units.values():
        require_valid_unit_state(unit, rules_module, valid_token_ids=valid_token_ids)
    return units


@dataclass
class GameRoom:
    game_id: str
    rules_module: RulesModule
    creator_client_id: str | None = None
    seq: int = 0
    connections: RoomConnectionManager = field(default_factory=RoomConnectionManager)
    tokens: Dict[str, TokenState] = field(default_factory=default_tokens)
    units: Dict[str, UnitState] = field(default_factory=dict)
    phase: Phase = "lobby"
    round: int = 0
    active_player_id: str | None = None
    initiative: InitiativeState | None = None
    undo_history_this_turn: List[UndoEntry] = field(default_factory=list)
    pending_undo_request: PendingUndoRequest | None = None
    undo_used_this_turn_player_ids: set[str] = field(default_factory=set)

    async def broadcast(self, event: Dict[str, Any], exclude_ws: WebSocket | None = None) -> None:
        await self.connections.broadcast(event, exclude_ws=exclude_ws)

    def __post_init__(self) -> None:
        if not self.units:
            self.units = default_units_for_rules_module(self.rules_module, self.tokens)


# In-memory room registry (MVP only)
ROOMS: Dict[str, GameRoom] = {}


def make_event(
    room: GameRoom,
    event_type: str,
    payload: Dict[str, Any],
    actor_player_id: str | None = None,
) -> Dict[str, Any]:
    room.seq += 1
    event = {
        "kind": "EVENT",
        "type": event_type,
        "seq": room.seq,
        "server_time": utc_now_iso(),
        "payload": payload,
    }
    if actor_player_id is not None:
        event["actor_player_id"] = actor_player_id
    return event


def create_room(
    game_id: str,
    creator_client_id: str | None = None,
    rules_module: RulesModule | None = None,
) -> GameRoom:
    room = GameRoom(
        game_id=game_id,
        creator_client_id=creator_client_id,
        rules_module=rules_module or require_rules_module(DEFAULT_RULES_MODULE_ID),
    )
    ROOMS[game_id] = room
    return room


def room_by_creator_client_id(creator_client_id: str) -> GameRoom | None:
    for room in ROOMS.values():
        if room.creator_client_id == creator_client_id:
            return room
    return None


def room_lobby_snapshot(room: GameRoom) -> LobbyRoomState:
    return {
        "game_id": room.game_id,
        "player_count": room.connections.player_count(),
        "phase": room.phase,
        "round": room.round,
        "rules_module": room.rules_module.snapshot(),
    }


def active_lobby_rooms_snapshot() -> List[LobbyRoomState]:
    active_rooms = [
        room_lobby_snapshot(room) for room in ROOMS.values() if room.connections.has_any()
    ]
    active_rooms.sort(key=lambda room: room["game_id"])
    return active_rooms


def room_players_snapshot(room: GameRoom) -> List[PlayerState]:
    return room.connections.players_snapshot()


def room_turn_snapshot(room: GameRoom) -> TurnState:
    return {
        "phase": room.phase,
        "round": room.round,
        "active_player_id": room.active_player_id,
    }


def room_rules_module_snapshot(room: GameRoom) -> RulesModuleSnapshot:
    return room.rules_module.snapshot()


def room_units_snapshot(room: GameRoom) -> List[UnitState]:
    return [room.units[unit_id] for unit_id in sorted(room.units)]


def room_initiative_snapshot(room: GameRoom) -> InitiativeState | None:
    if room.initiative is None:
        return None
    return {
        "winner_player_id": room.initiative["winner_player_id"],
        "loser_player_id": room.initiative["loser_player_id"],
        "winner_roll": room.initiative["winner_roll"],
        "loser_roll": room.initiative["loser_roll"],
        "chooser_choice": room.initiative["chooser_choice"],
        "first_player_id": room.initiative["first_player_id"],
        "second_player_id": room.initiative["second_player_id"],
    }


def room_undo_snapshot(room: GameRoom) -> UndoState:
    pending_request = room.pending_undo_request
    pending_snapshot: PendingUndoRequest | None
    if pending_request is None:
        pending_snapshot = None
    else:
        pending_snapshot = {
            "requester_player_id": pending_request["requester_player_id"],
            "responder_player_id": pending_request["responder_player_id"],
            "action_type": pending_request["action_type"],
            "token_id": pending_request["token_id"],
        }
    return {
        "pending_request": pending_snapshot,
        "undo_used_this_turn_player_ids": sorted(room.undo_used_this_turn_player_ids),
    }


def connected_player_ids(room: GameRoom) -> List[str]:
    return room.connections.connected_player_ids()
