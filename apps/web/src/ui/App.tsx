import React, { useEffect, useMemo, useRef, useState } from "react";
import { Board, type BoardToken } from "./Board";

type EventEnvelope = {
  kind: "EVENT";
  type: string;
  seq: number;
  server_time: string;
  payload: unknown;
};

type CommandEnvelope = {
  kind: "COMMAND";
  type: string;
  client_msg_id: string;
  payload: unknown;
};

type WsStatus = "DISCONNECTED" | "CONNECTING" | "CONNECTED";

function randomRoomId(): string {
  // Friendly enough for MVP; switch to UUIDs later.
  return Math.random().toString(16).slice(2, 10);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toBoardToken(value: unknown): BoardToken | null {
  if (!isRecord(value)) return null;

  const { id, label, x_mm, y_mm, r_mm } = value;
  if (typeof id !== "string" || typeof label !== "string") return null;
  if (typeof x_mm !== "number" || !Number.isInteger(x_mm)) return null;
  if (typeof y_mm !== "number" || !Number.isInteger(y_mm)) return null;
  if (typeof r_mm !== "number" || !Number.isInteger(r_mm)) return null;

  return { id, label, x_mm, y_mm, r_mm };
}

function isEventEnvelope(value: unknown): value is EventEnvelope {
  if (!isRecord(value)) return false;
  if (value.kind !== "EVENT") return false;
  if (typeof value.type !== "string") return false;
  if (!Number.isInteger(value.seq)) return false;
  if (typeof value.server_time !== "string") return false;
  return "payload" in value;
}

function extractHelloTokens(payload: unknown): BoardToken[] | null {
  if (!isRecord(payload)) return null;
  if (!Array.isArray(payload.tokens)) return null;

  const tokens = payload.tokens.map(toBoardToken);
  if (tokens.some((token) => token === null)) return null;
  return tokens as BoardToken[];
}

function extractMovedToken(payload: unknown): BoardToken | null {
  if (!isRecord(payload)) return null;
  return toBoardToken(payload.token);
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
  const [gameId, setGameId] = useState<string>(() => randomRoomId());
  const [createRoomPending, setCreateRoomPending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  const browserProtocol = window.location.protocol === "https:" ? "https" : "http";
  const wsProtocol = browserProtocol === "https" ? "wss" : "ws";
  const apiHost = window.location.hostname || "localhost";

  const apiBaseUrl = useMemo(() => `${browserProtocol}://${apiHost}:8000`, [apiHost, browserProtocol]);
  const wsUrl = useMemo(() => `${wsProtocol}://${apiHost}:8000/games/${gameId}/ws`, [apiHost, gameId, wsProtocol]);

  useEffect(() => {
    setEvents([]);
    setTokens([]);
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
          return;
        }

        if (parsed.type === "TOKEN_MOVED") {
          const movedToken = extractMovedToken(parsed.payload);
          if (movedToken) {
            setTokens((prev) => upsertToken(prev, movedToken));
          }
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

  function sendRollDice() {
    send({
      kind: "COMMAND",
      type: "ROLL_DICE",
      client_msg_id: crypto.randomUUID(),
      payload: { count: 3, sides: 6, modifier: 1 },
    });
  }

  async function createRoom() {
    setCreateRoomPending(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${apiBaseUrl}/games`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Could not create room (${response.status}).`);
      }

      const body = (await response.json()) as unknown;
      if (!isRecord(body) || typeof body.game_id !== "string") {
        throw new Error("Server returned an invalid room response.");
      }

      setGameId(body.game_id);
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
        <div style={{ color: theme.muted }}>WS: {status}</div>
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
          {createRoomPending ? "Creating..." : "Create Room"}
        </button>
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          Room:
          <input
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            style={{
              padding: 6,
              minWidth: 140,
              border: `1px solid ${theme.border}`,
              borderRadius: 6,
              background: theme.inputBg,
              color: theme.text,
            }}
          />
        </label>
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
        <small style={{ color: theme.muted }}>
          Tip: open this page in two browser windows with the same Room ID.
        </small>
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

      <main style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>
        <section>
          <Board
            tokens={tokens}
            canMoveTokens={status === "CONNECTED"}
            onMoveToken={sendMoveToken}
          />
        </section>

        <aside
          style={{
            border: `1px solid ${theme.border}`,
            borderRadius: 8,
            padding: 12,
            background: theme.surface,
          }}
        >
          <h2 style={{ marginTop: 0 }}>Event Log</h2>
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
                </div>
              ))}
          </div>
        </aside>
      </main>
    </div>
  );
}
