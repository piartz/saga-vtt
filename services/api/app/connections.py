from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, List

from fastapi import WebSocket, WebSocketDisconnect

from app.protocol_generated import Player as PlayerState


@dataclass
class RoomConnectionManager:
    sockets: List[WebSocket] = field(default_factory=list)
    players_by_ws_id: Dict[int, PlayerState] = field(default_factory=dict)

    def add(self, ws: WebSocket) -> PlayerState:
        player = self._create_player()
        self.sockets.append(ws)
        self.players_by_ws_id[id(ws)] = player
        return player

    def remove(self, ws: WebSocket) -> PlayerState | None:
        player = self.players_by_ws_id.pop(id(ws), None)
        if ws in self.sockets:
            self.sockets.remove(ws)
        return player

    def has_any(self) -> bool:
        return len(self.sockets) > 0

    def player_count(self) -> int:
        return len(self.players_by_ws_id)

    def players_snapshot(self) -> List[PlayerState]:
        return sorted(self.players_by_ws_id.values(), key=lambda player: player["id"])

    def connected_player_ids(self) -> List[str]:
        return [player["id"] for player in self.players_snapshot()]

    async def broadcast(self, event: Dict[str, Any], exclude_ws: WebSocket | None = None) -> None:
        for ws in list(self.sockets):
            if exclude_ws is not None and ws == exclude_ws:
                continue
            try:
                await ws.send_text(json.dumps(event))
            except WebSocketDisconnect:
                self.remove(ws)

    def _create_player(self) -> PlayerState:
        while True:
            player_id = secrets.token_hex(3)
            already_used = any(player["id"] == player_id for player in self.players_by_ws_id.values())
            if not already_used:
                break
        return {"id": player_id, "label": f"Player {player_id}"}
