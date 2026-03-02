import React, { useEffect, useMemo, useRef, useState } from "react";
import { Board } from "./Board";

type EventEnvelope = {
  kind: "EVENT";
  type: string;
  seq: number;
  server_time: string;
  payload: any;
};

type CommandEnvelope = {
  kind: "COMMAND";
  type: string;
  client_msg_id: string;
  payload: any;
};

type WsStatus = "DISCONNECTED" | "CONNECTING" | "CONNECTED";

function randomRoomId(): string {
  // Friendly enough for MVP; switch to UUIDs later.
  return Math.random().toString(16).slice(2, 10);
}

export function App() {
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
    <div style={{ fontFamily: "system-ui, sans-serif", padding: 16, display: "grid", gap: 16 }}>
      <header style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
        <h1 style={{ margin: 0 }}>Skirmish VTT</h1>
        <div style={{ opacity: 0.8 }}>WS: {status}</div>
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          Room:
          <input
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            style={{ padding: 6, minWidth: 140 }}
          />
        </label>
        <button onClick={sendPing} disabled={status !== "CONNECTED"}>
          Send PING
        </button>
        <small style={{ opacity: 0.7 }}>
          Tip: open this page in two browser windows with the same Room ID.
        </small>
      </header>

      <main style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>
        <section>
          <Board />
        </section>

        <aside style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
          <h2 style={{ marginTop: 0 }}>Event Log</h2>
          <div style={{ display: "grid", gap: 8, maxHeight: 520, overflow: "auto" }}>
            {events
              .slice()
              .reverse()
              .map((e) => (
                <div key={e.seq} style={{ border: "1px solid #eee", borderRadius: 6, padding: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <strong>{e.type}</strong>
                    <span style={{ opacity: 0.7 }}>#{e.seq}</span>
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.7 }}>{e.server_time}</div>
                  <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap" }}>
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
