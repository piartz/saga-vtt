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
        joined: Dict[str, Any] = ws1.receive_json()
        assert joined["type"] == "PLAYER_JOINED"

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


def test_roll_dice_is_authoritative_and_broadcast_to_all_clients() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        ws1.receive_json()
        ws2.receive_json()
        joined: Dict[str, Any] = ws1.receive_json()
        assert joined["type"] == "PLAYER_JOINED"

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "ROLL_DICE",
                "client_msg_id": "roll-1",
                "payload": {"count": 3, "sides": 6, "modifier": 1},
            }
        )

        event_1: Dict[str, Any] = ws1.receive_json()
        event_2: Dict[str, Any] = ws2.receive_json()

        assert event_1["type"] == "DICE_ROLLED"
        assert event_2["type"] == "DICE_ROLLED"
        assert event_1["payload"]["client_msg_id"] == "roll-1"
        assert event_1["payload"]["count"] == 3
        assert event_1["payload"]["sides"] == 6
        assert event_1["payload"]["modifier"] == 1
        assert event_1["payload"]["notation"] == "3d6+1"
        assert len(event_1["payload"]["rolls"]) == 3
        assert all(1 <= die <= 6 for die in event_1["payload"]["rolls"])
        assert event_1["payload"]["total"] == sum(event_1["payload"]["rolls"]) + 1
        assert event_2["payload"] == event_1["payload"]


def test_player_presence_join_and_leave_events() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws1:
        hello_1: Dict[str, Any] = ws1.receive_json()
        assert hello_1["type"] == "HELLO"
        assert len(hello_1["payload"]["players"]) == 1
        first_player = hello_1["payload"]["players"][0]
        assert isinstance(first_player["id"], str)

        with client.websocket_connect(f"/games/{game_id}/ws") as ws2:
            hello_2: Dict[str, Any] = ws2.receive_json()
            assert hello_2["type"] == "HELLO"
            assert len(hello_2["payload"]["players"]) == 2

            joined: Dict[str, Any] = ws1.receive_json()
            assert joined["type"] == "PLAYER_JOINED"
            joined_player = joined["payload"]["player"]
            assert joined_player["id"] != first_player["id"]
            assert joined_player in hello_2["payload"]["players"]

        left: Dict[str, Any] = ws1.receive_json()
        assert left["type"] == "PLAYER_LEFT"
        assert left["payload"]["player_id"] == joined_player["id"]


def test_roll_dice_rejects_invalid_payload() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws:
        ws.receive_json()
        ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ROLL_DICE",
                "client_msg_id": "roll-invalid",
                "payload": {"count": 0, "sides": 6},
            }
        )

        event: Dict[str, Any] = ws.receive_json()
        assert event["type"] == "ERROR"
        assert event["payload"]["message"] == "ROLL_DICE count must be an integer between 1 and 20."
