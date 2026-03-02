import React, { useEffect, useMemo, useRef, useState } from "react";
import { Board } from "./Board";

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
  const [gameId, setGameId] = useState<string>(() => randomRoomId());

  const wsRef = useRef<WebSocket | null>(null);

  const wsUrl = useMemo(() => `ws://localhost:8000/games/${gameId}/ws`, [gameId]);

  useEffect(() => {
    setEvents([]);
    setStatus("CONNECTING");

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setStatus("CONNECTED");

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as EventEnvelope;
        setEvents((prev) => [...prev, data]);
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
        <small style={{ color: theme.muted }}>
          Tip: open this page in two browser windows with the same Room ID.
        </small>
      </header>

      <main style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>
        <section>
          <Board />
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
