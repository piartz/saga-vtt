import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Board, type ActivationType, type BoardToken } from "./Board";

type EventEnvelope = {
  kind: "EVENT";
  type: string;
  seq: number;
  server_time: string;
  actor_player_id?: string;
  payload: unknown;
};

type CommandEnvelope = {
  kind: "COMMAND";
  type: string;
  client_msg_id: string;
  payload: unknown;
};

type WsStatus = "DISCONNECTED" | "CONNECTING" | "CONNECTED";
type EventLogMode = "READABLE" | "ADVANCED";

type PresencePlayer = {
  id: string;
  label: string;
};

type LobbyRoom = {
  game_id: string;
  player_count: number;
  phase: "lobby" | "running";
  round: number;
};

type TurnState = {
  phase: "lobby" | "running";
  round: number;
  active_player_id: string | null;
};

type TurnChoice = "FIRST" | "SECOND";

type InitiativeState = {
  winner_player_id: string;
  loser_player_id: string;
  winner_roll: number;
  loser_roll: number;
  chooser_choice: TurnChoice | null;
  first_player_id: string | null;
  second_player_id: string | null;
};

type UndoActionType = "MOVE_TOKEN" | "ACTIVATE_TOKEN";

type UndoRequest = {
  requester_player_id: string;
  responder_player_id: string;
  action_type: UndoActionType;
  token_id: string;
};

type UndoState = {
  pending_request: UndoRequest | null;
  undo_used_this_turn_player_ids: string[];
};

function roomIdFromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  const room = params.get("room");
  if (!room) return null;
  const normalized = room.trim();
  if (normalized.length === 0) return null;
  return normalized;
}

function createFallbackClientId(): string {
  return `client-${Math.random().toString(16).slice(2, 12)}`;
}

function getOrCreateClientId(): string {
  const key = "saga_vtt_client_id";
  try {
    const existing = window.localStorage.getItem(key)?.trim();
    if (existing) return existing;
    const generated =
      typeof window.crypto !== "undefined" && "randomUUID" in window.crypto
        ? window.crypto.randomUUID()
        : createFallbackClientId();
    window.localStorage.setItem(key, generated);
    return generated;
  } catch {
    return createFallbackClientId();
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isActivationType(value: unknown): value is ActivationType {
  return value === "move" || value === "charge" || value === "shoot" || value === "rest";
}

function toBoardToken(value: unknown): BoardToken | null {
  if (!isRecord(value)) return null;

  const { id, label, x_mm, y_mm, r_mm, activation_count_this_turn, last_activation_type } = value;
  if (typeof id !== "string" || typeof label !== "string") return null;
  if (typeof x_mm !== "number" || !Number.isInteger(x_mm)) return null;
  if (typeof y_mm !== "number" || !Number.isInteger(y_mm)) return null;
  if (typeof r_mm !== "number" || !Number.isInteger(r_mm)) return null;
  if (
    typeof activation_count_this_turn !== "number" ||
    !Number.isInteger(activation_count_this_turn) ||
    activation_count_this_turn < 0
  ) {
    return null;
  }
  if (!(last_activation_type === null || isActivationType(last_activation_type))) return null;

  return { id, label, x_mm, y_mm, r_mm, activation_count_this_turn, last_activation_type };
}

function isEventEnvelope(value: unknown): value is EventEnvelope {
  if (!isRecord(value)) return false;
  if (value.kind !== "EVENT") return false;
  if (typeof value.type !== "string") return false;
  if (!Number.isInteger(value.seq)) return false;
  if (typeof value.server_time !== "string") return false;
  if ("actor_player_id" in value && typeof value.actor_player_id !== "string") return false;
  return "payload" in value;
}

function extractHelloTokens(payload: unknown): BoardToken[] | null {
  if (!isRecord(payload)) return null;
  if (!Array.isArray(payload.tokens)) return null;

  const tokens = payload.tokens.map(toBoardToken);
  if (tokens.some((token) => token === null)) return null;
  return tokens as BoardToken[];
}

function toPresencePlayer(value: unknown): PresencePlayer | null {
  if (!isRecord(value)) return null;

  const { id, label } = value;
  if (typeof id !== "string" || typeof label !== "string") return null;
  return { id, label };
}

function toLobbyRoom(value: unknown): LobbyRoom | null {
  if (!isRecord(value)) return null;
  const { game_id, player_count, phase, round } = value;
  if (typeof game_id !== "string") return null;
  if (typeof player_count !== "number" || !Number.isInteger(player_count) || player_count < 0) return null;
  if (!(phase === "lobby" || phase === "running")) return null;
  if (typeof round !== "number" || !Number.isInteger(round) || round < 0) return null;
  return { game_id, player_count, phase, round };
}

function extractLobbyRooms(value: unknown): LobbyRoom[] | null {
  if (!isRecord(value) || !Array.isArray(value.rooms)) return null;
  const rooms = value.rooms.map(toLobbyRoom);
  if (rooms.some((room) => room === null)) return null;
  return rooms as LobbyRoom[];
}

function extractHelloPlayers(payload: unknown): PresencePlayer[] | null {
  if (!isRecord(payload)) return null;
  if (!Array.isArray(payload.players)) return null;

  const players = payload.players.map(toPresencePlayer);
  if (players.some((player) => player === null)) return null;
  return players as PresencePlayer[];
}

function extractMovedToken(payload: unknown): BoardToken | null {
  if (!isRecord(payload)) return null;
  return toBoardToken(payload.token);
}

function extractTokensSnapshot(payload: unknown): BoardToken[] | null {
  if (!isRecord(payload) || !Array.isArray(payload.tokens)) return null;
  const tokens = payload.tokens.map(toBoardToken);
  if (tokens.some((token) => token === null)) return null;
  return tokens as BoardToken[];
}

function extractJoinedPlayer(payload: unknown): PresencePlayer | null {
  if (!isRecord(payload)) return null;
  return toPresencePlayer(payload.player);
}

function extractLeftPlayerId(payload: unknown): string | null {
  if (!isRecord(payload)) return null;
  return typeof payload.player_id === "string" ? payload.player_id : null;
}

function toTurnState(value: unknown): TurnState | null {
  if (!isRecord(value)) return null;
  if (value.phase !== "lobby" && value.phase !== "running") return null;
  const round = value.round;
  if (typeof round !== "number" || !Number.isInteger(round) || round < 0) return null;
  if (!(value.active_player_id === null || typeof value.active_player_id === "string")) return null;
  return {
    phase: value.phase,
    round,
    active_player_id: value.active_player_id,
  };
}

function extractHelloTurn(payload: unknown): TurnState | null {
  if (!isRecord(payload)) return null;
  return toTurnState(payload.turn);
}

function extractTurnFromEvent(payload: unknown): TurnState | null {
  if (!isRecord(payload)) return null;
  return toTurnState(payload.turn);
}

function toInitiativeState(value: unknown): InitiativeState | null {
  if (!isRecord(value)) return null;
  const {
    winner_player_id,
    loser_player_id,
    winner_roll,
    loser_roll,
    chooser_choice,
    first_player_id,
    second_player_id,
  } = value;
  if (typeof winner_player_id !== "string") return null;
  if (typeof loser_player_id !== "string") return null;
  if (typeof winner_roll !== "number" || !Number.isInteger(winner_roll)) return null;
  if (typeof loser_roll !== "number" || !Number.isInteger(loser_roll)) return null;
  if (!(chooser_choice === null || chooser_choice === "FIRST" || chooser_choice === "SECOND")) return null;
  if (!(first_player_id === null || typeof first_player_id === "string")) return null;
  if (!(second_player_id === null || typeof second_player_id === "string")) return null;
  return {
    winner_player_id,
    loser_player_id,
    winner_roll,
    loser_roll,
    chooser_choice,
    first_player_id,
    second_player_id,
  };
}

function extractHelloInitiative(payload: unknown): InitiativeState | null {
  if (!isRecord(payload)) return null;
  if (payload.initiative === null || payload.initiative === undefined) return null;
  return toInitiativeState(payload.initiative);
}

function extractEventInitiative(payload: unknown): InitiativeState | null {
  if (!isRecord(payload)) return null;
  return toInitiativeState(payload.initiative);
}

function extractHelloSelfPlayerId(payload: unknown): string | null {
  if (!isRecord(payload)) return null;
  return typeof payload.self_player_id === "string" ? payload.self_player_id : null;
}

function toUndoRequest(value: unknown): UndoRequest | null {
  if (!isRecord(value)) return null;
  const { requester_player_id, responder_player_id, action_type, token_id } = value;
  if (typeof requester_player_id !== "string") return null;
  if (typeof responder_player_id !== "string") return null;
  if (action_type !== "MOVE_TOKEN" && action_type !== "ACTIVATE_TOKEN") return null;
  if (typeof token_id !== "string") return null;
  return { requester_player_id, responder_player_id, action_type, token_id };
}

function toUndoState(value: unknown): UndoState | null {
  if (!isRecord(value)) return null;
  const pendingRequestRaw = value.pending_request;
  const usedByRaw = value.undo_used_this_turn_player_ids;
  if (!(pendingRequestRaw === null || pendingRequestRaw === undefined || isRecord(pendingRequestRaw))) return null;
  if (!Array.isArray(usedByRaw)) return null;
  if (!usedByRaw.every((playerId) => typeof playerId === "string")) return null;
  const pendingRequest =
    pendingRequestRaw === null || pendingRequestRaw === undefined ? null : toUndoRequest(pendingRequestRaw);
  if (pendingRequestRaw !== null && pendingRequestRaw !== undefined && pendingRequest === null) return null;
  return {
    pending_request: pendingRequest,
    undo_used_this_turn_player_ids: [...usedByRaw],
  };
}

function extractHelloUndo(payload: unknown): UndoState | null {
  if (!isRecord(payload)) return null;
  if (payload.undo === null || payload.undo === undefined) return null;
  return toUndoState(payload.undo);
}

function extractEventUndo(payload: unknown): UndoState | null {
  if (!isRecord(payload)) return null;
  return toUndoState(payload.undo);
}

function upsertToken(prev: BoardToken[], next: BoardToken): BoardToken[] {
  let found = false;
  const updated = prev.map((token) => {
    if (token.id !== next.id) return token;
    found = true;
    return next;
  });

  if (!found) updated.push(next);
  return updated;
}

function upsertPlayer(prev: PresencePlayer[], next: PresencePlayer): PresencePlayer[] {
  let found = false;
  const updated = prev.map((player) => {
    if (player.id !== next.id) return player;
    found = true;
    return next;
  });

  if (!found) updated.push(next);
  return updated.sort((a, b) => a.id.localeCompare(b.id));
}

function upsertKnownPlayerMap(
  prev: Record<string, PresencePlayer>,
  next: PresencePlayer | PresencePlayer[]
): Record<string, PresencePlayer> {
  const updated = { ...prev };
  const players = Array.isArray(next) ? next : [next];
  for (const player of players) {
    updated[player.id] = player;
  }
  return updated;
}

function playerNameForEvent(
  playerId: string | undefined,
  knownPlayersById: Record<string, PresencePlayer>
): string {
  if (!playerId) return "System";
  return knownPlayersById[playerId]?.label ?? `Player ${playerId}`;
}

function maybeYouSuffix(playerId: string | undefined, localPlayerId: string | null): string {
  return playerId !== undefined && localPlayerId !== null && playerId === localPlayerId ? " (you)" : "";
}

function formatEventSummary(
  event: EventEnvelope,
  knownPlayersById: Record<string, PresencePlayer>
): string {
  const actorName = playerNameForEvent(event.actor_player_id, knownPlayersById);
  const payload = isRecord(event.payload) ? event.payload : {};

  if (event.type === "HELLO") {
    const gameId = typeof payload.game_id === "string" ? payload.game_id : "unknown";
    const tokenCount = Array.isArray(payload.tokens) ? payload.tokens.length : 0;
    const playerCount = Array.isArray(payload.players) ? payload.players.length : 0;
    return `Connected to room ${gameId}. ${playerCount} player(s) online, ${tokenCount} token(s) loaded.`;
  }

  if (event.type === "PLAYER_JOINED") {
    const joinedPlayer = toPresencePlayer(payload.player);
    const joinedName = joinedPlayer?.label ?? actorName;
    return `${joinedName} joined the room.`;
  }

  if (event.type === "PLAYER_LEFT") {
    const leftPlayerId = typeof payload.player_id === "string" ? payload.player_id : undefined;
    const leftName = playerNameForEvent(leftPlayerId, knownPlayersById);
    return `${leftName} left the room.`;
  }

  if (event.type === "PONG") {
    return `${actorName} sent a ping and received PONG.`;
  }

  if (event.type === "TOKEN_MOVED") {
    const movedToken = toBoardToken(payload.token);
    if (!movedToken) return `${actorName} moved a token.`;
    return `${actorName} moved token ${movedToken.label} to (${movedToken.x_mm}, ${movedToken.y_mm}) mm.`;
  }

  if (event.type === "TOKEN_ACTIVATED") {
    const changedToken = toBoardToken(payload.token);
    if (!changedToken) return `${actorName} activated a token.`;
    const activationName = changedToken.last_activation_type ?? "unknown";
    return `${actorName} activated ${changedToken.label} with ${activationName} (${changedToken.activation_count_this_turn}x this turn).`;
  }

  if (event.type === "UNDO_REQUESTED") {
    const request = toUndoRequest(payload.request);
    if (!request) return `${actorName} requested an undo.`;
    const tokenName = request.token_id;
    const actionLabel = request.action_type === "MOVE_TOKEN" ? "movement" : "activation";
    const requesterName = playerNameForEvent(request.requester_player_id, knownPlayersById);
    return `${requesterName} requested undo for ${actionLabel} on token ${tokenName}.`;
  }

  if (event.type === "UNDO_APPLIED") {
    const request = toUndoRequest(payload.request);
    if (!request) return `${actorName} accepted an undo request.`;
    const tokenName = request.token_id;
    const actionLabel = request.action_type === "MOVE_TOKEN" ? "movement" : "activation";
    return `${actorName} accepted undo. ${actionLabel} on token ${tokenName} was reverted.`;
  }

  if (event.type === "UNDO_REJECTED") {
    const request = toUndoRequest(payload.request);
    if (!request) return `${actorName} rejected an undo request.`;
    const tokenName = request.token_id;
    const actionLabel = request.action_type === "MOVE_TOKEN" ? "movement" : "activation";
    return `${actorName} rejected undo for ${actionLabel} on token ${tokenName}.`;
  }

  if (event.type === "UNDO_CANCELLED") {
    const reason = typeof payload.reason === "string" ? payload.reason : "unknown";
    return `Undo request was cancelled (${reason}).`;
  }

  if (event.type === "DICE_ROLLED") {
    const notation = typeof payload.notation === "string" ? payload.notation : "dice";
    const total = typeof payload.total === "number" ? payload.total : "?";
    const rolls = Array.isArray(payload.rolls)
      ? payload.rolls.filter((roll) => typeof roll === "number").join(", ")
      : "";
    if (rolls) {
      return `${actorName} rolled ${notation}: [${rolls}] = ${total}.`;
    }
    return `${actorName} rolled ${notation}: total ${total}.`;
  }

  if (event.type === "GAME_STARTED") {
    const turn = extractTurnFromEvent(payload);
    if (!turn) return `${actorName} started the game.`;
    const activeName = playerNameForEvent(turn.active_player_id ?? undefined, knownPlayersById);
    return `${actorName} started the game. Round ${turn.round}, active player: ${activeName}.`;
  }

  if (event.type === "INITIATIVE_ROLLED") {
    const initiative = extractEventInitiative(payload);
    if (!initiative) return `${actorName} rolled initiative.`;
    const winnerName = playerNameForEvent(initiative.winner_player_id, knownPlayersById);
    return `${winnerName} won initiative (${initiative.winner_roll} vs ${initiative.loser_roll}).`;
  }

  if (event.type === "TURN_ORDER_CHOSEN") {
    const initiative = extractEventInitiative(payload);
    if (!initiative) return `${actorName} chose turn order.`;
    const firstName = playerNameForEvent(initiative.first_player_id ?? undefined, knownPlayersById);
    const secondName = playerNameForEvent(initiative.second_player_id ?? undefined, knownPlayersById);
    return `${actorName} chose to go ${initiative.chooser_choice}. First: ${firstName}. Second: ${secondName}.`;
  }

  if (event.type === "INITIATIVE_RESET") {
    const reason = typeof payload.reason === "string" ? payload.reason : "unknown";
    return `Initiative selection reset (${reason}).`;
  }

  if (event.type === "TURN_CHANGED") {
    const turn = extractTurnFromEvent(payload);
    if (!turn) return `${actorName} ended the turn.`;
    const activeName = playerNameForEvent(turn.active_player_id ?? undefined, knownPlayersById);
    return `${actorName} ended the turn. Round ${turn.round}, active player: ${activeName}.`;
  }

  if (event.type === "ERROR") {
    const message = typeof payload.message === "string" ? payload.message : "Unknown error.";
    return `${actorName} received an error: ${message}`;
  }

  return `${actorName} triggered ${event.type}.`;
}

export function App() {
  const theme = {
    bg: "#0f1115",
    surface: "#171b24",
    surfaceAlt: "#1d2330",
    border: "#2c3446",
    text: "#e7ebf3",
    muted: "#aab4c8",
    inputBg: "#111722",
    accent: "#7ea2ff",
  } as const;

  const [status, setStatus] = useState<WsStatus>("DISCONNECTED");
  const [events, setEvents] = useState<EventEnvelope[]>([]);
  const [tokens, setTokens] = useState<BoardToken[]>([]);
  const [players, setPlayers] = useState<PresencePlayer[]>([]);
  const [knownPlayersById, setKnownPlayersById] = useState<Record<string, PresencePlayer>>({});
  const [turn, setTurn] = useState<TurnState | null>(null);
  const [initiative, setInitiative] = useState<InitiativeState | null>(null);
  const [undo, setUndo] = useState<UndoState | null>(null);
  const [localPlayerId, setLocalPlayerId] = useState<string | null>(null);
  const [eventLogMode, setEventLogMode] = useState<EventLogMode>("READABLE");
  const [confirmMoves, setConfirmMoves] = useState(true);
  const [gameId, setGameId] = useState<string | null>(() => roomIdFromUrl());
  const [joinRoomInput, setJoinRoomInput] = useState<string>(() => roomIdFromUrl() ?? "");
  const [lobbyRooms, setLobbyRooms] = useState<LobbyRoom[]>([]);
  const [lobbyRoomsPending, setLobbyRoomsPending] = useState(false);
  const [lobbyErrorMessage, setLobbyErrorMessage] = useState<string | null>(null);
  const [createRoomPending, setCreateRoomPending] = useState(false);
  const [inviteCopyMessage, setInviteCopyMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const clientId = useMemo(() => getOrCreateClientId(), []);

  const browserProtocol = window.location.protocol === "https:" ? "https" : "http";
  const wsProtocol = browserProtocol === "https" ? "wss" : "ws";
  const apiHost = window.location.hostname || "localhost";

  const apiBaseUrl = useMemo(() => `${browserProtocol}://${apiHost}:8000`, [apiHost, browserProtocol]);
  const wsUrl = useMemo(
    () => (gameId ? `${wsProtocol}://${apiHost}:8000/games/${gameId}/ws` : null),
    [apiHost, gameId, wsProtocol]
  );

  const refreshLobbyRooms = useCallback(
    async (showSpinner: boolean) => {
      if (showSpinner) setLobbyRoomsPending(true);

      try {
        const response = await fetch(`${apiBaseUrl}/rooms`);
        if (!response.ok) {
          throw new Error(`Could not load active rooms (${response.status}).`);
        }
        const body = (await response.json()) as unknown;
        const parsed = extractLobbyRooms(body);
        if (parsed === null) {
          throw new Error("Server returned an invalid active room list.");
        }
        setLobbyRooms(parsed);
        setLobbyErrorMessage(null);
      } catch (err) {
        if (err instanceof Error) {
          setLobbyErrorMessage(err.message);
        } else {
          setLobbyErrorMessage("Could not load active rooms.");
        }
      } finally {
        if (showSpinner) setLobbyRoomsPending(false);
      }
    },
    [apiBaseUrl]
  );

  useEffect(() => {
    void refreshLobbyRooms(true);
    const intervalId = window.setInterval(() => {
      void refreshLobbyRooms(false);
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [refreshLobbyRooms]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (gameId) {
      params.set("room", gameId);
    } else {
      params.delete("room");
    }
    const nextQuery = params.toString();
    const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}${window.location.hash}`;
    window.history.replaceState({}, "", nextUrl);
  }, [gameId]);

  useEffect(() => {
    if (!wsUrl) {
      setEvents([]);
      setTokens([]);
      setPlayers([]);
      setKnownPlayersById({});
      setTurn(null);
      setInitiative(null);
      setLocalPlayerId(null);
      setStatus("DISCONNECTED");
      setInviteCopyMessage(null);
      const currentWs = wsRef.current;
      if (currentWs) {
        try {
          currentWs.close();
        } finally {
          wsRef.current = null;
        }
      }
      return;
    }

    setEvents([]);
    setTokens([]);
    setPlayers([]);
    setKnownPlayersById({});
    setTurn(null);
    setInitiative(null);
    setUndo(null);
    setLocalPlayerId(null);
    setStatus("CONNECTING");

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setStatus("CONNECTED");

    ws.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data) as unknown;
        if (!isEventEnvelope(parsed)) return;

        setEvents((prev) => [...prev, parsed]);

        if (parsed.type === "HELLO") {
          const helloTokens = extractHelloTokens(parsed.payload);
          if (helloTokens) setTokens(helloTokens);
          const helloPlayers = extractHelloPlayers(parsed.payload);
          if (helloPlayers) {
            setPlayers(helloPlayers);
            setKnownPlayersById((prev) => upsertKnownPlayerMap(prev, helloPlayers));
          }
          const helloTurn = extractHelloTurn(parsed.payload);
          if (helloTurn) setTurn(helloTurn);
          setInitiative(extractHelloInitiative(parsed.payload));
          setUndo(extractHelloUndo(parsed.payload));
          setLocalPlayerId(extractHelloSelfPlayerId(parsed.payload));
          return;
        }

        if (parsed.type === "TOKEN_MOVED") {
          const movedToken = extractMovedToken(parsed.payload);
          if (movedToken) {
            setTokens((prev) => upsertToken(prev, movedToken));
          }
          return;
        }

        if (parsed.type === "TOKEN_ACTIVATED") {
          const changedToken = extractMovedToken(parsed.payload);
          if (changedToken) {
            setTokens((prev) => upsertToken(prev, changedToken));
          }
          return;
        }

        if (parsed.type === "PLAYER_JOINED") {
          const joinedPlayer = extractJoinedPlayer(parsed.payload);
          if (joinedPlayer) {
            setPlayers((prev) => upsertPlayer(prev, joinedPlayer));
            setKnownPlayersById((prev) => upsertKnownPlayerMap(prev, joinedPlayer));
          }
          return;
        }

        if (parsed.type === "PLAYER_LEFT") {
          const leftPlayerId = extractLeftPlayerId(parsed.payload);
          if (leftPlayerId) {
            setPlayers((prev) => prev.filter((player) => player.id !== leftPlayerId));
          }
          return;
        }

        if (parsed.type === "GAME_STARTED" || parsed.type === "TURN_CHANGED") {
          const nextTurn = extractTurnFromEvent(parsed.payload);
          if (nextTurn) setTurn(nextTurn);
          const tokenSnapshot = extractTokensSnapshot(parsed.payload);
          if (tokenSnapshot) setTokens(tokenSnapshot);
          const nextUndo = extractEventUndo(parsed.payload);
          if (nextUndo) setUndo(nextUndo);
          return;
        }

        if (parsed.type === "INITIATIVE_ROLLED" || parsed.type === "TURN_ORDER_CHOSEN") {
          const nextInitiative = extractEventInitiative(parsed.payload);
          if (nextInitiative) setInitiative(nextInitiative);
          return;
        }

        if (parsed.type === "INITIATIVE_RESET") {
          setInitiative(null);
          return;
        }

        if (
          parsed.type === "UNDO_REQUESTED" ||
          parsed.type === "UNDO_APPLIED" ||
          parsed.type === "UNDO_REJECTED" ||
          parsed.type === "UNDO_CANCELLED"
        ) {
          const nextUndo = extractEventUndo(parsed.payload);
          if (nextUndo) setUndo(nextUndo);
          const tokenSnapshot = extractMovedToken(parsed.payload);
          if (tokenSnapshot) setTokens((prev) => upsertToken(prev, tokenSnapshot));
          return;
        }
      } catch {
        // ignore
      }
    };

    ws.onclose = () => setStatus("DISCONNECTED");
    ws.onerror = () => setStatus("DISCONNECTED");

    return () => {
      try {
        ws.close();
      } finally {
        wsRef.current = null;
      }
    };
  }, [wsUrl]);

  function send(cmd: CommandEnvelope) {
    const ws = wsRef.current;
    if (!ws || status !== "CONNECTED") return;
    ws.send(JSON.stringify(cmd));
  }

  function sendPing() {
    send({
      kind: "COMMAND",
      type: "PING",
      client_msg_id: crypto.randomUUID(),
      payload: { client_time: new Date().toISOString() },
    });
  }

  function sendMoveToken(tokenId: string, xMm: number, yMm: number) {
    send({
      kind: "COMMAND",
      type: "MOVE_TOKEN",
      client_msg_id: crypto.randomUUID(),
      payload: { token_id: tokenId, x_mm: xMm, y_mm: yMm },
    });
  }

  function sendActivateToken(tokenId: string, activationType: ActivationType) {
    send({
      kind: "COMMAND",
      type: "ACTIVATE_TOKEN",
      client_msg_id: crypto.randomUUID(),
      payload: { token_id: tokenId, activation_type: activationType },
    });
  }

  function sendRollDice() {
    send({
      kind: "COMMAND",
      type: "ROLL_DICE",
      client_msg_id: crypto.randomUUID(),
      payload: { count: 3, sides: 6, modifier: 1 },
    });
  }

  function sendStartGame() {
    send({
      kind: "COMMAND",
      type: "START_GAME",
      client_msg_id: crypto.randomUUID(),
      payload: {},
    });
  }

  function sendEndTurn() {
    send({
      kind: "COMMAND",
      type: "END_TURN",
      client_msg_id: crypto.randomUUID(),
      payload: {},
    });
  }

  function sendChooseTurnOrder(choice: TurnChoice) {
    send({
      kind: "COMMAND",
      type: "CHOOSE_TURN_ORDER",
      client_msg_id: crypto.randomUUID(),
      payload: { choice },
    });
  }

  function sendRequestUndo() {
    send({
      kind: "COMMAND",
      type: "REQUEST_UNDO",
      client_msg_id: crypto.randomUUID(),
      payload: {},
    });
  }

  function sendRespondUndoRequest(accept: boolean) {
    send({
      kind: "COMMAND",
      type: "RESPOND_UNDO_REQUEST",
      client_msg_id: crypto.randomUUID(),
      payload: { accept },
    });
  }

  async function createRoom() {
    setCreateRoomPending(true);
    setErrorMessage(null);
    setInfoMessage(null);

    try {
      const response = await fetch(`${apiBaseUrl}/games`, {
        method: "POST",
        headers: { "X-Client-Id": clientId },
      });
      if (!response.ok) {
        throw new Error(`Could not create room (${response.status}).`);
      }

      const body = (await response.json()) as unknown;
      if (!isRecord(body) || typeof body.game_id !== "string") {
        throw new Error("Server returned an invalid room response.");
      }

      const wasCreated = body.created === true;
      setGameId(body.game_id);
      setJoinRoomInput(body.game_id);
      setInfoMessage(wasCreated ? "Room created. Joining now." : "You already have an active room. Rejoining it.");
      void refreshLobbyRooms(false);
    } catch (err) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Could not create room.");
      }
    } finally {
      setCreateRoomPending(false);
    }
  }

  async function copyInviteLink() {
    if (!gameId) return;
    setInviteCopyMessage(null);
    const inviteUrl = `${window.location.origin}${window.location.pathname}?room=${encodeURIComponent(gameId)}`;
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setInviteCopyMessage("Invite link copied.");
    } catch {
      setInviteCopyMessage("Could not copy invite link.");
    }
  }

  function joinRoom(candidateId: string) {
    const trimmed = candidateId.trim();
    if (trimmed.length === 0) {
      setErrorMessage("Room id is required.");
      return;
    }
    setErrorMessage(null);
    setGameId(trimmed);
    setJoinRoomInput(trimmed);
  }

  const activePlayerName =
    turn?.active_player_id !== null && turn?.active_player_id !== undefined
      ? knownPlayersById[turn.active_player_id]?.label ?? `Player ${turn.active_player_id}`
      : "none";
  const initiativeWinnerName =
    initiative !== null
      ? knownPlayersById[initiative.winner_player_id]?.label ?? `Player ${initiative.winner_player_id}`
      : null;
  const initiativeLoserName =
    initiative !== null
      ? knownPlayersById[initiative.loser_player_id]?.label ?? `Player ${initiative.loser_player_id}`
      : null;
  const isInitiativeWinner = initiative !== null && localPlayerId === initiative.winner_player_id;
  const isInitiativeLoser = initiative !== null && localPlayerId === initiative.loser_player_id;
  const turnOrderResolved = initiative !== null && initiative.chooser_choice !== null;
  const amFirstPlayer =
    turnOrderResolved && initiative !== null && localPlayerId === initiative.first_player_id;
  const amSecondPlayer =
    turnOrderResolved && initiative !== null && localPlayerId === initiative.second_player_id;
  const turnOrderMessage = amFirstPlayer
    ? "You are the first player."
    : amSecondPlayer
      ? "You are the second player."
      : null;
  const pendingUndoRequest = undo?.pending_request ?? null;
  const undoUsedByMe =
    localPlayerId !== null ? (undo?.undo_used_this_turn_player_ids ?? []).includes(localPlayerId) : false;
  const isRunningActivePlayer =
    turn?.phase === "running" && localPlayerId !== null && turn.active_player_id === localPlayerId;
  const isUndoRequester =
    pendingUndoRequest !== null && localPlayerId !== null && pendingUndoRequest.requester_player_id === localPlayerId;
  const isUndoResponder =
    pendingUndoRequest !== null && localPlayerId !== null && pendingUndoRequest.responder_player_id === localPlayerId;
  const canRequestUndo =
    status === "CONNECTED" && isRunningActivePlayer && pendingUndoRequest === null && !undoUsedByMe;
  const pendingUndoActionLabel =
    pendingUndoRequest !== null
      ? pendingUndoRequest.action_type === "MOVE_TOKEN"
        ? "movement"
        : "activation"
      : null;
  const pendingUndoTokenLabel =
    pendingUndoRequest !== null
      ? tokens.find((token) => token.id === pendingUndoRequest.token_id)?.label ?? pendingUndoRequest.token_id
      : null;

  if (gameId === null) {
    return (
      <div
        style={{
          fontFamily: "system-ui, sans-serif",
          padding: 16,
          display: "grid",
          gap: 16,
          minHeight: "100dvh",
          boxSizing: "border-box",
          background: theme.bg,
          color: theme.text,
        }}
      >
        <header style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <h1 style={{ margin: 0 }}>Skirmish VTT Lobby</h1>
          <button
            onClick={createRoom}
            disabled={createRoomPending}
            style={{
              padding: "6px 10px",
              borderRadius: 6,
              border: `1px solid ${theme.border}`,
              background: theme.surfaceAlt,
              color: theme.text,
              cursor: createRoomPending ? "not-allowed" : "pointer",
            }}
          >
            {createRoomPending ? "Creating..." : "Create & Join Room"}
          </button>
          <button
            onClick={() => void refreshLobbyRooms(true)}
            disabled={lobbyRoomsPending}
            style={{
              padding: "6px 10px",
              borderRadius: 6,
              border: `1px solid ${theme.border}`,
              background: theme.surfaceAlt,
              color: theme.text,
              cursor: lobbyRoomsPending ? "not-allowed" : "pointer",
            }}
          >
            {lobbyRoomsPending ? "Refreshing..." : "Refresh Rooms"}
          </button>
        </header>

        {errorMessage && (
          <div
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: "8px 12px",
              background: theme.surfaceAlt,
              color: "#ffb3b3",
            }}
          >
            {errorMessage}
          </div>
        )}
        {lobbyErrorMessage && (
          <div
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: "8px 12px",
              background: theme.surfaceAlt,
              color: "#ffb3b3",
            }}
          >
            {lobbyErrorMessage}
          </div>
        )}
        {infoMessage && (
          <div
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: "8px 12px",
              background: theme.surfaceAlt,
              color: theme.text,
            }}
          >
            {infoMessage}
          </div>
        )}

        <main style={{ display: "grid", gridTemplateColumns: "1fr minmax(280px, 360px)", gap: 16 }}>
          <section
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: 12,
              background: theme.surface,
            }}
          >
            <h2 style={{ marginTop: 0 }}>Active Rooms</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {lobbyRooms.map((room) => (
                <div
                  key={room.game_id}
                  style={{
                    border: `1px solid ${theme.border}`,
                    borderRadius: 8,
                    padding: 10,
                    background: theme.surfaceAlt,
                    display: "grid",
                    gap: 8,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                    <strong>Room {room.game_id}</strong>
                    <span style={{ fontSize: 12, color: theme.muted }}>
                      {room.player_count} player{room.player_count === 1 ? "" : "s"}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: theme.muted }}>
                      {room.phase} | Round {room.round}
                    </span>
                    <button
                      onClick={() => joinRoom(room.game_id)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: 6,
                        border: `1px solid ${theme.border}`,
                        background: theme.surface,
                        color: theme.text,
                        cursor: "pointer",
                        fontSize: 12,
                      }}
                    >
                      Join Room
                    </button>
                  </div>
                </div>
              ))}
              {lobbyRooms.length === 0 && (
                <div style={{ fontSize: 13, color: theme.muted }}>
                  No active rooms yet. Create one to start, then share the invite link.
                </div>
              )}
            </div>
          </section>

          <aside
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: 12,
              background: theme.surface,
              display: "grid",
              alignContent: "start",
              gap: 10,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 0 }}>Join by Room ID</h2>
            <input
              value={joinRoomInput}
              onChange={(e) => setJoinRoomInput(e.target.value)}
              placeholder="e.g. a1b2c3d4"
              style={{
                padding: 8,
                border: `1px solid ${theme.border}`,
                borderRadius: 6,
                background: theme.inputBg,
                color: theme.text,
              }}
            />
            <button
              onClick={() => joinRoom(joinRoomInput)}
              style={{
                padding: "6px 10px",
                borderRadius: 6,
                border: `1px solid ${theme.border}`,
                background: theme.surfaceAlt,
                color: theme.text,
                cursor: "pointer",
              }}
            >
              Join Room
            </button>
            <div style={{ fontSize: 12, color: theme.muted }}>
              Opening a room sets URL as `?room=&lt;id&gt;` so links are shareable.
            </div>
          </aside>
        </main>
      </div>
    );
  }

  return (
    <div
      style={{
        fontFamily: "system-ui, sans-serif",
        padding: 16,
        display: "grid",
        gap: 16,
        minHeight: "100dvh",
        boxSizing: "border-box",
        background: theme.bg,
        color: theme.text,
      }}
    >
      <header style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
        <h1 style={{ margin: 0 }}>Skirmish VTT</h1>
        <div style={{ color: theme.muted }}>Room: {gameId}</div>
        <div style={{ color: theme.muted }}>WS: {status}</div>
        <div style={{ color: theme.muted }}>
          Turn:{" "}
          {turn
            ? `${turn.phase === "running" ? `Round ${turn.round}` : "Lobby"} | Active: ${activePlayerName}`
            : "unknown"}
        </div>
        <button
          onClick={() => setGameId(null)}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.surfaceAlt,
            color: theme.text,
            cursor: "pointer",
          }}
        >
          Back To Lobby
        </button>
        <button
          onClick={copyInviteLink}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.surfaceAlt,
            color: theme.text,
            cursor: "pointer",
          }}
        >
          Copy Invite Link
        </button>
        <button
          onClick={sendPing}
          disabled={status !== "CONNECTED"}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.surfaceAlt,
            color: theme.text,
            cursor: status === "CONNECTED" ? "pointer" : "not-allowed",
          }}
        >
          Send PING
        </button>
        <button
          onClick={sendRollDice}
          disabled={status !== "CONNECTED"}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.surfaceAlt,
            color: theme.text,
            cursor: status === "CONNECTED" ? "pointer" : "not-allowed",
          }}
        >
          Roll 3d6+1
        </button>
        <button
          onClick={sendStartGame}
          disabled={status !== "CONNECTED" || turn?.phase === "running" || initiative?.chooser_choice === null}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.surfaceAlt,
            color: theme.text,
            cursor:
              status === "CONNECTED" && turn?.phase !== "running" && initiative?.chooser_choice !== null
                ? "pointer"
                : "not-allowed",
          }}
        >
          New Game
        </button>
        <button
          onClick={sendEndTurn}
          disabled={status !== "CONNECTED" || turn?.phase !== "running"}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.surfaceAlt,
            color: theme.text,
            cursor: status === "CONNECTED" && turn?.phase === "running" ? "pointer" : "not-allowed",
          }}
        >
          End Turn
        </button>
        <label style={{ display: "flex", gap: 6, alignItems: "center", color: theme.muted }}>
          <input
            type="checkbox"
            checked={confirmMoves}
            onChange={(e) => setConfirmMoves(e.target.checked)}
          />
          Confirm Movement
        </label>
      </header>

      {errorMessage && (
        <div
          style={{
            border: `1px solid ${theme.border}`,
            borderRadius: 8,
            padding: "8px 12px",
            background: theme.surfaceAlt,
            color: "#ffb3b3",
          }}
        >
          {errorMessage}
        </div>
      )}
      {inviteCopyMessage && (
        <div
          style={{
            border: `1px solid ${theme.border}`,
            borderRadius: 8,
            padding: "8px 12px",
            background: theme.surfaceAlt,
            color: theme.text,
          }}
        >
          {inviteCopyMessage}
        </div>
      )}

      <main style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>
        <section>
          <Board
            tokens={tokens}
            canMoveTokens={status === "CONNECTED"}
            canActivateTokens={status === "CONNECTED"}
            confirmMoves={confirmMoves}
            onMoveToken={sendMoveToken}
            onActivateToken={sendActivateToken}
          />
        </section>

        <aside
          style={{
            border: `1px solid ${theme.border}`,
            borderRadius: 8,
            padding: 12,
            background: theme.surface,
            display: "grid",
            gap: 12,
          }}
        >
          {initiative && initiative.chooser_choice === null && (
            <section
              style={{
                border: `1px solid ${theme.border}`,
                borderRadius: 10,
                padding: 12,
                background:
                  "linear-gradient(130deg, rgba(126,162,255,0.22) 0%, rgba(23,27,36,0.95) 60%, rgba(23,27,36,1) 100%)",
              }}
            >
              <h2 style={{ marginTop: 0, marginBottom: 6 }}>Who Goes First</h2>
              <div style={{ display: "grid", gap: 8 }}>
                <div style={{ fontSize: 13, color: theme.muted }}>
                  Initiative roll: <strong>{initiativeWinnerName}</strong> {initiative.winner_roll} vs{" "}
                  <strong>{initiativeLoserName}</strong> {initiative.loser_roll}
                </div>
                {isInitiativeWinner && (
                  <div style={{ display: "grid", gap: 8 }}>
                    <div style={{ fontSize: 14 }}>You won initiative. Choose your turn order:</div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        onClick={() => sendChooseTurnOrder("FIRST")}
                        style={{
                          padding: "6px 10px",
                          borderRadius: 6,
                          border: `1px solid ${theme.border}`,
                          background: theme.surfaceAlt,
                          color: theme.text,
                          cursor: "pointer",
                        }}
                      >
                        Go First
                      </button>
                      <button
                        onClick={() => sendChooseTurnOrder("SECOND")}
                        style={{
                          padding: "6px 10px",
                          borderRadius: 6,
                          border: `1px solid ${theme.border}`,
                          background: theme.surfaceAlt,
                          color: theme.text,
                          cursor: "pointer",
                        }}
                      >
                        Go Second
                      </button>
                    </div>
                  </div>
                )}
                {isInitiativeLoser && (
                  <div style={{ fontSize: 14, color: theme.text }}>
                    Waiting for your opponent to choose...
                  </div>
                )}
              </div>
            </section>
          )}
          {turnOrderResolved && turnOrderMessage && (
            <section
              style={{
                border: `1px solid ${theme.border}`,
                borderRadius: 10,
                padding: 12,
                background: theme.surfaceAlt,
              }}
            >
              <h2 style={{ marginTop: 0, marginBottom: 6 }}>Turn Order</h2>
              <div style={{ fontSize: 14 }}>{turnOrderMessage}</div>
            </section>
          )}
          <section
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 10,
              padding: 12,
              background: theme.surfaceAlt,
              display: "grid",
              gap: 8,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 2 }}>Undo Action</h2>
            <div style={{ fontSize: 12, color: theme.muted }}>
              Undo only applies to board actions (movement or activation). One request per player turn.
            </div>
            <button
              onClick={sendRequestUndo}
              disabled={!canRequestUndo}
              style={{
                padding: "6px 10px",
                borderRadius: 6,
                border: `1px solid ${theme.border}`,
                background: theme.surface,
                color: theme.text,
                cursor: canRequestUndo ? "pointer" : "not-allowed",
              }}
            >
              Request Undo
            </button>
            {isUndoRequester && pendingUndoActionLabel && pendingUndoTokenLabel && (
              <div style={{ fontSize: 13 }}>
                Undo requested for {pendingUndoActionLabel} on token <strong>{pendingUndoTokenLabel}</strong>. Waiting
                for your opponent...
              </div>
            )}
            {isUndoResponder && pendingUndoActionLabel && pendingUndoTokenLabel && (
              <div style={{ display: "grid", gap: 8 }}>
                <div style={{ fontSize: 13 }}>
                  Opponent requested undo for {pendingUndoActionLabel} on token{" "}
                  <strong>{pendingUndoTokenLabel}</strong>.
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={() => sendRespondUndoRequest(true)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 6,
                      border: `1px solid ${theme.border}`,
                      background: theme.surface,
                      color: theme.text,
                      cursor: "pointer",
                    }}
                  >
                    Accept Undo
                  </button>
                  <button
                    onClick={() => sendRespondUndoRequest(false)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 6,
                      border: `1px solid ${theme.border}`,
                      background: theme.surface,
                      color: theme.text,
                      cursor: "pointer",
                    }}
                  >
                    Reject Undo
                  </button>
                </div>
              </div>
            )}
            {!isUndoRequester && !isUndoResponder && undoUsedByMe && isRunningActivePlayer && (
              <div style={{ fontSize: 13 }}>Undo already used this turn.</div>
            )}
          </section>

          <section>
            <h2 style={{ marginTop: 0 }}>Players</h2>
            <div style={{ display: "grid", gap: 8 }}>
              {players.map((player) => (
                <div
                  key={player.id}
                  style={{
                    border: `1px solid ${theme.border}`,
                    borderRadius: 6,
                    padding: "8px 10px",
                    background: theme.surfaceAlt,
                    outline:
                      turn?.active_player_id === player.id ? `1px solid ${theme.accent}` : "1px solid transparent",
                  }}
                >
                  <div>
                    {player.label}
                    {maybeYouSuffix(player.id, localPlayerId)}
                    {turn?.active_player_id === player.id ? " (active)" : ""}
                  </div>
                  <div style={{ fontSize: 12, color: theme.muted }}>{player.id}</div>
                </div>
              ))}
              {players.length === 0 && (
                <div style={{ fontSize: 12, color: theme.muted }}>No players connected.</div>
              )}
            </div>
          </section>

          <section>
            <h2 style={{ marginTop: 0 }}>Event Log</h2>
            <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
              <button
                onClick={() => setEventLogMode("READABLE")}
                style={{
                  padding: "4px 10px",
                  borderRadius: 6,
                  border: `1px solid ${theme.border}`,
                  background: eventLogMode === "READABLE" ? theme.accent : theme.surfaceAlt,
                  color: eventLogMode === "READABLE" ? "#0f1115" : theme.text,
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                Readable
              </button>
              <button
                onClick={() => setEventLogMode("ADVANCED")}
                style={{
                  padding: "4px 10px",
                  borderRadius: 6,
                  border: `1px solid ${theme.border}`,
                  background: eventLogMode === "ADVANCED" ? theme.accent : theme.surfaceAlt,
                  color: eventLogMode === "ADVANCED" ? "#0f1115" : theme.text,
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                Advanced (JSON)
              </button>
            </div>
            <div style={{ display: "grid", gap: 8, maxHeight: 520, overflow: "auto" }}>
              {events
                .slice()
                .reverse()
                .map((e) => (
                  <div
                    key={e.seq}
                    style={{
                      border: `1px solid ${theme.border}`,
                      borderRadius: 6,
                      padding: 8,
                      background: theme.surfaceAlt,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                      <strong>{e.type}</strong>
                      <span style={{ color: theme.muted }}>#{e.seq}</span>
                    </div>
                    <div style={{ fontSize: 12, color: theme.muted }}>{e.server_time}</div>
                    {e.actor_player_id && (
                      <div style={{ fontSize: 12, color: theme.muted }}>
                        By: {knownPlayersById[e.actor_player_id]?.label ?? `Player ${e.actor_player_id}`} (
                        {e.actor_player_id}
                        {maybeYouSuffix(e.actor_player_id, localPlayerId)})
                      </div>
                    )}
                    {eventLogMode === "READABLE" ? (
                      <div style={{ marginTop: 6, fontSize: 13, color: theme.text }}>
                        {formatEventSummary(e, knownPlayersById)}
                      </div>
                    ) : (
                      <pre
                        style={{
                          margin: 0,
                          fontSize: 12,
                          whiteSpace: "pre-wrap",
                          color: theme.accent,
                        }}
                      >
                        {JSON.stringify(e.payload, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}
