"""
AUTO-GENERATED FILE - DO NOT EDIT

This file is generated from schemas/protocol.json
Run 'poetry run python tools/generate_types.py' to regenerate
"""

from typing import List, Literal, TypedDict

ActivationType = Literal["move", "charge", "shoot", "rest"]
Phase = Literal["lobby", "running"]
TurnChoice = Literal["FIRST", "SECOND"]
UndoActionType = Literal["MOVE_TOKEN", "ACTIVATE_TOKEN"]
class Player(TypedDict):
    id: str
    label: str

class Token(TypedDict):
    id: str
    name: str
    x_mm: int
    y_mm: int
    radius_mm: int
    activation_count_this_turn: int
    last_activation_type: ActivationType | None

class Board(TypedDict):
    width_mm: int
    height_mm: int

class TurnState(TypedDict):
    phase: Phase
    round: int
    active_player_id: str | None

class InitiativeState(TypedDict):
    winner_player_id: str
    loser_player_id: str
    winner_roll: int
    loser_roll: int
    chooser_choice: TurnChoice | None
    first_player_id: str | None
    second_player_id: str | None

class UndoRequest(TypedDict):
    requester_player_id: str
    responder_player_id: str
    action_type: UndoActionType
    token_id: str

class UndoState(TypedDict):
    pending_request: UndoRequest | None
    undo_used_this_turn_player_ids: List[str]


# Command Payloads

class PINGPayload(TypedDict):
    pass

class MOVE_TOKENPayload(TypedDict):
    token_id: str
    x_mm: int
    y_mm: int

class ACTIVATE_TOKENPayload(TypedDict):
    token_id: str
    activation_type: ActivationType

class START_GAMEPayload(TypedDict):
    pass

class CHOOSE_TURN_ORDERPayload(TypedDict):
    choice: TurnChoice

class END_TURNPayload(TypedDict):
    pass

class REQUEST_UNDOPayload(TypedDict):
    pass

class RESPOND_UNDO_REQUESTPayload(TypedDict):
    accept: bool

class ROLL_DICEPayload(TypedDict, total=False):
    count: int
    sides: int
    modifier: int

CommandType = Literal["PING", "MOVE_TOKEN", "ACTIVATE_TOKEN", "START_GAME", "CHOOSE_TURN_ORDER", "END_TURN", "REQUEST_UNDO", "RESPOND_UNDO_REQUEST", "ROLL_DICE"]


# Event Payloads

class PONGPayload(TypedDict):
    pass

class HELLOPayload(TypedDict):
    game_id: str
    protocol_version: int
    board: Board
    tokens: List[Token]
    players: List[Player]
    self_player_id: str
    turn: TurnState
    initiative: InitiativeState | None
    undo: UndoState

class PLAYER_JOINEDPayload(TypedDict):
    player: Player

class PLAYER_LEFTPayload(TypedDict):
    player_id: str

class INITIATIVE_ROLLEDPayload(TypedDict):
    initiative: InitiativeState

class TURN_ORDER_CHOSENPayload(TypedDict):
    initiative: InitiativeState

class GAME_STARTEDPayload(TypedDict):
    turn: TurnState
    undo: UndoState

class INITIATIVE_RESETPayload(TypedDict):
    reason: Literal["player_joined", "player_left"]

class TURN_CHANGEDPayload(TypedDict):
    turn: TurnState
    tokens: List[Token]
    undo: UndoState

class TOKEN_MOVEDPayload(TypedDict):
    token: Token
    client_msg_id: str

class TOKEN_ACTIVATEDPayload(TypedDict):
    token: Token
    client_msg_id: str

class UNDO_REQUESTEDPayload(TypedDict):
    request: UndoRequest
    undo: UndoState

class UNDO_APPLIEDPayload(TypedDict):
    request: UndoRequest
    token: Token
    undo: UndoState

class UNDO_REJECTEDPayload(TypedDict):
    request: UndoRequest
    undo: UndoState

class UNDO_CANCELLEDPayload(TypedDict):
    reason: Literal["player_left"]
    undo: UndoState

class DICE_ROLLEDPayload(TypedDict):
    count: int
    sides: int
    modifier: int
    rolls: List[int]
    total: int
    notation: str
    client_msg_id: str

class ERRORPayload(TypedDict, total=False):
    message: str
    client_msg_id: str

EventType = Literal["PONG", "HELLO", "PLAYER_JOINED", "PLAYER_LEFT", "INITIATIVE_ROLLED", "TURN_ORDER_CHOSEN", "GAME_STARTED", "INITIATIVE_RESET", "TURN_CHANGED", "TOKEN_MOVED", "TOKEN_ACTIVATED", "UNDO_REQUESTED", "UNDO_APPLIED", "UNDO_REJECTED", "UNDO_CANCELLED", "DICE_ROLLED", "ERROR"]
