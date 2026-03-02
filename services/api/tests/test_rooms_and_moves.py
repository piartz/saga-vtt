from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import ROOMS, app


@pytest.fixture(autouse=True)
def clear_rooms() -> None:
    ROOMS.clear()
    yield
    ROOMS.clear()


def test_create_game_room() -> None:
    client = TestClient(app)
    response = client.post("/games")

    assert response.status_code == 200
    body = response.json()

    assert isinstance(body["game_id"], str)
    assert body["game_id"] in ROOMS
    assert body["protocol_version"] == 1
    assert body["board"] == {"width_mm": 800, "height_mm": 500}
    assert len(body["tokens"]) >= 2


def test_move_token_is_authoritative_and_broadcast_to_all_clients() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        hello_2: Dict[str, Any] = ws2.receive_json()

        assert hello_1["type"] == "HELLO"
        assert hello_2["type"] == "HELLO"

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "MOVE_TOKEN",
                "client_msg_id": "move-1",
                "payload": {"token_id": "A", "x_mm": 222, "y_mm": 111},
            }
        )

        event_1: Dict[str, Any] = ws1.receive_json()
        event_2: Dict[str, Any] = ws2.receive_json()

        assert event_1["type"] == "TOKEN_MOVED"
        assert event_2["type"] == "TOKEN_MOVED"
        assert event_1["payload"]["token"]["id"] == "A"
        assert event_1["payload"]["token"]["x_mm"] == 222
        assert event_1["payload"]["token"]["y_mm"] == 111
        assert event_2["payload"]["token"]["x_mm"] == 222
        assert event_2["payload"]["token"]["y_mm"] == 111
        assert ROOMS[game_id].tokens["A"]["x_mm"] == 222
        assert ROOMS[game_id].tokens["A"]["y_mm"] == 111
