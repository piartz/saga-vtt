from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class GameRoom:
    game_id: str
    seq: int = 0
    connections: List[WebSocket] = field(default_factory=list)

    async def broadcast(self, event: Dict[str, Any]) -> None:
        for ws in list(self.connections):
            await ws.send_text(json.dumps(event))


# In-memory room registry (MVP only)
ROOMS: Dict[str, GameRoom] = {}


app = FastAPI(title="Skirmish VTT API", version="0.1.0")

# Dev-friendly CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "time": utc_now_iso()}


@app.websocket("/games/{game_id}/ws")
async def game_ws(ws: WebSocket, game_id: str) -> None:
    await ws.accept()

    room = ROOMS.get(game_id)
    if room is None:
        room = GameRoom(game_id=game_id)
        ROOMS[game_id] = room

    room.connections.append(ws)

    # Initial hello event
    room.seq += 1
    await ws.send_text(
        json.dumps(
            {
                "kind": "EVENT",
                "type": "HELLO",
                "seq": room.seq,
                "server_time": utc_now_iso(),
                "payload": {"game_id": game_id, "protocol_version": 1},
            }
        )
    )

    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                room.seq += 1
                await ws.send_text(
                    json.dumps(
                        {
                            "kind": "EVENT",
                            "type": "ERROR",
                            "seq": room.seq,
                            "server_time": utc_now_iso(),
                            "payload": {"message": "Invalid JSON"},
                        }
                    )
                )
                continue

            # MVP: only PING -> PONG
            if data.get("kind") == "COMMAND" and data.get("type") == "PING":
                room.seq += 1
                await room.broadcast(
                    {
                        "kind": "EVENT",
                        "type": "PONG",
                        "seq": room.seq,
                        "server_time": utc_now_iso(),
                        "payload": {"echo": data.get("payload", {})},
                    }
                )
            else:
                room.seq += 1
                await ws.send_text(
                    json.dumps(
                        {
                            "kind": "EVENT",
                            "type": "ERROR",
                            "seq": room.seq,
                            "server_time": utc_now_iso(),
                            "payload": {"message": "Unknown command", "received": data},
                        }
                    )
                )

    except WebSocketDisconnect:
        # Remove connection
        if ws in room.connections:
            room.connections.remove(ws)
        # Cleanup empty room
        if not room.connections:
            ROOMS.pop(game_id, None)
