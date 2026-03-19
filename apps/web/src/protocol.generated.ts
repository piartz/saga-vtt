/**
 * AUTO-GENERATED FILE - DO NOT EDIT
 *
 * This file is generated from schemas/protocol.json
 * Run 'pnpm generate-types' to regenerate
 */

export type ActivationType = "move" | "charge" | "shoot" | "rest";

export type Phase = "lobby" | "running";

export type TurnChoice = "FIRST" | "SECOND";

export type UndoActionType = "MOVE_TOKEN" | "ACTIVATE_TOKEN";

export interface Player {
  id: string;
  label: string;
}

export interface Token {
  id: string;
  name: string;
  x_mm: number;
  y_mm: number;
  radius_mm: number;
  activation_count_this_turn: number;
  last_activation_type: ActivationType | null;
}

export interface Board {
  width_mm: number;
  height_mm: number;
}

export interface TurnState {
  phase: Phase;
  round: number;
  active_player_id: string | null;
}

export interface InitiativeState {
  winner_player_id: string;
  loser_player_id: string;
  winner_roll: number;
  loser_roll: number;
  chooser_choice: TurnChoice | null;
  first_player_id: string | null;
  second_player_id: string | null;
}

export interface UndoRequest {
  requester_player_id: string;
  responder_player_id: string;
  action_type: UndoActionType;
  token_id: string;
}

export interface UndoState {
  pending_request: UndoRequest | null;
  undo_used_this_turn_player_ids: string[];
}

// Command Payloads

export type PINGPayload = Record<string, never>;

export type MOVE_TOKENPayload = {
  token_id: string;
  x_mm: number;
  y_mm: number;
};

export type ACTIVATE_TOKENPayload = {
  token_id: string;
  activation_type: ActivationType;
};

export type START_GAMEPayload = Record<string, never>;

export type CHOOSE_TURN_ORDERPayload = {
  choice: TurnChoice;
};

export type END_TURNPayload = Record<string, never>;

export type REQUEST_UNDOPayload = Record<string, never>;

export type RESPOND_UNDO_REQUESTPayload = {
  accept: boolean;
};

export type ROLL_DICEPayload = {
  count: number;
  sides: number;
  modifier?: number;
};

export type CommandType = "PING" | "MOVE_TOKEN" | "ACTIVATE_TOKEN" | "START_GAME" | "CHOOSE_TURN_ORDER" | "END_TURN" | "REQUEST_UNDO" | "RESPOND_UNDO_REQUEST" | "ROLL_DICE";

export interface CommandEnvelope {
  kind: "COMMAND";
  type: CommandType;
  client_msg_id: string;
  payload: unknown;
}

// Event Payloads

export type PONGPayload = Record<string, never>;

export type HELLOPayload = {
  game_id: string;
  protocol_version: number;
  board: Board;
  tokens: Token[];
  players: Player[];
  self_player_id: string;
  turn: TurnState;
  initiative: InitiativeState | null;
  undo: UndoState;
};

export type PLAYER_JOINEDPayload = {
  player: Player;
};

export type PLAYER_LEFTPayload = {
  player_id: string;
};

export type INITIATIVE_ROLLEDPayload = {
  initiative: InitiativeState;
};

export type TURN_ORDER_CHOSENPayload = {
  initiative: InitiativeState;
};

export type GAME_STARTEDPayload = {
  turn: TurnState;
  undo: UndoState;
};

export type INITIATIVE_RESETPayload = {
  reason: "player_joined" | "player_left";
};

export type TURN_CHANGEDPayload = {
  turn: TurnState;
  tokens: Token[];
  undo: UndoState;
};

export type TOKEN_MOVEDPayload = {
  token: Token;
  client_msg_id: string;
};

export type TOKEN_ACTIVATEDPayload = {
  token: Token;
  client_msg_id: string;
};

export type UNDO_REQUESTEDPayload = {
  request: UndoRequest;
  undo: UndoState;
};

export type UNDO_APPLIEDPayload = {
  request: UndoRequest;
  token: Token;
  undo: UndoState;
};

export type UNDO_REJECTEDPayload = {
  request: UndoRequest;
  undo: UndoState;
};

export type UNDO_CANCELLEDPayload = {
  reason: "player_left";
  undo: UndoState;
};

export type DICE_ROLLEDPayload = {
  count: number;
  sides: number;
  modifier: number;
  rolls: number[];
  total: number;
  notation: string;
  client_msg_id: string;
};

export type ERRORPayload = {
  message: string;
  client_msg_id?: string;
};

export type EventType = "PONG" | "HELLO" | "PLAYER_JOINED" | "PLAYER_LEFT" | "INITIATIVE_ROLLED" | "TURN_ORDER_CHOSEN" | "GAME_STARTED" | "INITIATIVE_RESET" | "TURN_CHANGED" | "TOKEN_MOVED" | "TOKEN_ACTIVATED" | "UNDO_REQUESTED" | "UNDO_APPLIED" | "UNDO_REJECTED" | "UNDO_CANCELLED" | "DICE_ROLLED" | "ERROR";

export interface EventEnvelope {
  kind: "EVENT";
  type: EventType;
  seq: number;
  server_time: string;
  actor_player_id?: string;
  payload: unknown;
}
