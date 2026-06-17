import asyncio
import json
from typing import Any

from fastapi import WebSocketDisconnect

from app.connections import RoomConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent_texts: list[str] = []

    async def send_text(self, message: str) -> None:
        self.sent_texts.append(message)


class DisconnectingWebSocket(FakeWebSocket):
    async def send_text(self, message: str) -> None:
        raise WebSocketDisconnect()


def sent_payloads(ws: FakeWebSocket) -> list[dict[str, Any]]:
    return [json.loads(message) for message in ws.sent_texts]


def test_connection_manager_assigns_players_and_tracks_snapshots() -> None:
    manager = RoomConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    player1 = manager.add(ws1)
    player2 = manager.add(ws2)

    assert player1["id"] != player2["id"]
    assert player1["label"] == f"Player {player1['id']}"
    assert player2["label"] == f"Player {player2['id']}"
    assert manager.has_any() is True
    assert manager.player_count() == 2
    assert {player["id"] for player in manager.players_snapshot()} == {
        player1["id"],
        player2["id"],
    }
    assert manager.connected_player_ids() == sorted([player1["id"], player2["id"]])

    assert manager.remove(ws1) == player1
    assert manager.player_count() == 1
    assert manager.connected_player_ids() == [player2["id"]]

    assert manager.remove(ws1) is None
    assert manager.remove(ws2) == player2
    assert manager.has_any() is False


def test_connection_manager_broadcasts_with_exclusion_and_removes_stale_sockets() -> None:
    manager = RoomConnectionManager()
    active_ws = FakeWebSocket()
    excluded_ws = FakeWebSocket()
    stale_ws = DisconnectingWebSocket()

    active_player = manager.add(active_ws)
    excluded_player = manager.add(excluded_ws)
    stale_player = manager.add(stale_ws)

    event = {"kind": "EVENT", "type": "TEST_EVENT", "payload": {"ok": True}}

    asyncio.run(manager.broadcast(event, exclude_ws=excluded_ws))

    assert sent_payloads(active_ws) == [event]
    assert sent_payloads(excluded_ws) == []
    assert manager.player_count() == 2
    assert set(manager.connected_player_ids()) == {active_player["id"], excluded_player["id"]}
    assert stale_player["id"] not in manager.connected_player_ids()
