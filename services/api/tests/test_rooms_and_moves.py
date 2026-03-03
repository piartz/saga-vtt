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
    assert body["tokens"][0]["activation_count_this_turn"] == 0
    assert body["tokens"][0]["last_activation_type"] is None


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
        actor_player_id = hello_1["payload"]["players"][0]["id"]

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
        assert event_1["actor_player_id"] == actor_player_id
        assert event_2["actor_player_id"] == actor_player_id
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
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        actor_player_id = hello_1["payload"]["players"][0]["id"]
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
        assert event_1["actor_player_id"] == actor_player_id
        assert event_2["actor_player_id"] == actor_player_id


def test_activate_token_is_authoritative_and_broadcast_to_all_clients() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        hello_2: Dict[str, Any] = ws2.receive_json()
        joined: Dict[str, Any] = ws1.receive_json()
        assert joined["type"] == "PLAYER_JOINED"
        player_1 = hello_1["payload"]["players"][0]["id"]
        player_2 = joined["payload"]["player"]["id"]
        expected_first_active = min(player_1, player_2)
        assert player_2 in [player["id"] for player in hello_2["payload"]["players"]]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-activation-test",
                "payload": {},
            }
        )
        ws1.receive_json()
        ws2.receive_json()

        active_ws = ws1 if expected_first_active == player_1 else ws2
        actor_player_id = expected_first_active

        active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-1",
                "payload": {"token_id": "A", "activation_type": "move"},
            }
        )

        event_1: Dict[str, Any] = ws1.receive_json()
        event_2: Dict[str, Any] = ws2.receive_json()

        assert event_1["type"] == "TOKEN_ACTIVATED"
        assert event_2["type"] == "TOKEN_ACTIVATED"
        assert event_1["payload"]["token"]["id"] == "A"
        assert event_1["payload"]["token"]["activation_count_this_turn"] == 1
        assert event_1["payload"]["token"]["last_activation_type"] == "move"
        assert event_1["payload"]["client_msg_id"] == "activate-1"
        assert event_2["payload"] == event_1["payload"]
        assert event_1["actor_player_id"] == actor_player_id
        assert event_2["actor_player_id"] == actor_player_id
        assert ROOMS[game_id].tokens["A"]["activation_count_this_turn"] == 1
        assert ROOMS[game_id].tokens["A"]["last_activation_type"] == "move"

        active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-2",
                "payload": {"token_id": "A", "activation_type": "shoot"},
            }
        )
        second_event_1: Dict[str, Any] = ws1.receive_json()
        second_event_2: Dict[str, Any] = ws2.receive_json()
        assert second_event_1["type"] == "TOKEN_ACTIVATED"
        assert second_event_2["type"] == "TOKEN_ACTIVATED"
        assert second_event_1["payload"]["token"]["activation_count_this_turn"] == 2
        assert second_event_1["payload"]["token"]["last_activation_type"] == "shoot"
        assert second_event_2["payload"]["token"]["activation_count_this_turn"] == 2
        assert second_event_2["payload"]["token"]["last_activation_type"] == "shoot"


def test_rest_activation_requires_no_prior_activations_this_turn() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws:
        ws.receive_json()
        ws.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-rest-rule",
                "payload": {},
            }
        )
        ws.receive_json()

        ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-move-before-rest",
                "payload": {"token_id": "A", "activation_type": "move"},
            }
        )
        first_activation: Dict[str, Any] = ws.receive_json()
        assert first_activation["type"] == "TOKEN_ACTIVATED"
        assert first_activation["payload"]["token"]["activation_count_this_turn"] == 1
        assert first_activation["payload"]["token"]["last_activation_type"] == "move"

        ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-rest-after-move",
                "payload": {"token_id": "A", "activation_type": "rest"},
            }
        )
        rest_error: Dict[str, Any] = ws.receive_json()
        assert rest_error["type"] == "ERROR"
        assert "cannot activate to rest after prior activations this turn" in rest_error["payload"]["message"]
        assert ROOMS[game_id].tokens["A"]["activation_count_this_turn"] == 1
        assert ROOMS[game_id].tokens["A"]["last_activation_type"] == "move"

        ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-rest-fresh-token",
                "payload": {"token_id": "B", "activation_type": "rest"},
            }
        )
        rest_ok: Dict[str, Any] = ws.receive_json()
        assert rest_ok["type"] == "TOKEN_ACTIVATED"
        assert rest_ok["payload"]["token"]["id"] == "B"
        assert rest_ok["payload"]["token"]["activation_count_this_turn"] == 1
        assert rest_ok["payload"]["token"]["last_activation_type"] == "rest"


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
            assert joined["actor_player_id"] == joined_player["id"]

        left: Dict[str, Any] = ws1.receive_json()
        assert left["type"] == "PLAYER_LEFT"
        assert left["payload"]["player_id"] == joined_player["id"]
        assert left["actor_player_id"] == joined_player["id"]


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


def test_activate_token_rejects_when_game_not_running() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws:
        ws.receive_json()
        ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-before-start",
                "payload": {"token_id": "A", "activation_type": "move"},
            }
        )

        event: Dict[str, Any] = ws.receive_json()
        assert event["type"] == "ERROR"
        assert event["payload"]["message"] == "ACTIVATE_TOKEN is only allowed while game is running."


def test_start_game_and_end_turn_broadcasts_turn_state() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        hello_2: Dict[str, Any] = ws2.receive_json()
        joined: Dict[str, Any] = ws1.receive_json()

        player_1 = hello_1["payload"]["players"][0]["id"]
        player_2 = joined["payload"]["player"]["id"]
        assert player_2 in [player["id"] for player in hello_2["payload"]["players"]]

        expected_first_active = min(player_1, player_2)
        expected_second_active = max(player_1, player_2)

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-1",
                "payload": {},
            }
        )

        started_1: Dict[str, Any] = ws1.receive_json()
        started_2: Dict[str, Any] = ws2.receive_json()

        assert started_1["type"] == "GAME_STARTED"
        assert started_2["type"] == "GAME_STARTED"
        assert started_1["actor_player_id"] == player_1
        assert started_1["payload"]["turn"] == {
            "phase": "running",
            "round": 1,
            "active_player_id": expected_first_active,
        }

        first_active_ws = ws1 if expected_first_active == player_1 else ws2
        second_active_ws = ws2 if expected_first_active == player_1 else ws1

        first_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-before-end-turn",
                "payload": {"token_id": "A", "activation_type": "charge"},
            }
        )
        activate_1: Dict[str, Any] = ws1.receive_json()
        activate_2: Dict[str, Any] = ws2.receive_json()
        assert activate_1["type"] == "TOKEN_ACTIVATED"
        assert activate_2["type"] == "TOKEN_ACTIVATED"
        assert activate_1["payload"]["token"]["activation_count_this_turn"] == 1
        assert activate_1["payload"]["token"]["last_activation_type"] == "charge"

        first_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "END_TURN",
                "client_msg_id": "end-1",
                "payload": {},
            }
        )

        changed_1: Dict[str, Any] = ws1.receive_json()
        changed_2: Dict[str, Any] = ws2.receive_json()

        assert changed_1["type"] == "TURN_CHANGED"
        assert changed_2["type"] == "TURN_CHANGED"
        assert changed_1["payload"]["turn"] == {
            "phase": "running",
            "round": 1,
            "active_player_id": expected_second_active,
        }
        tokens_after_end_1 = changed_1["payload"]["tokens"]
        tokens_after_end_2 = changed_2["payload"]["tokens"]
        token_a_1 = next(token for token in tokens_after_end_1 if token["id"] == "A")
        token_a_2 = next(token for token in tokens_after_end_2 if token["id"] == "A")
        assert token_a_1["activation_count_this_turn"] == 0
        assert token_a_1["last_activation_type"] is None
        assert token_a_2["activation_count_this_turn"] == 0
        assert token_a_2["last_activation_type"] is None

        second_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "END_TURN",
                "client_msg_id": "end-2",
                "payload": {},
            }
        )

        wrapped_1: Dict[str, Any] = ws1.receive_json()
        wrapped_2: Dict[str, Any] = ws2.receive_json()

        assert wrapped_1["type"] == "TURN_CHANGED"
        assert wrapped_2["type"] == "TURN_CHANGED"
        assert wrapped_1["payload"]["turn"] == {
            "phase": "running",
            "round": 2,
            "active_player_id": expected_first_active,
        }


def test_non_active_player_cannot_end_turn_or_take_running_actions() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        joined: Dict[str, Any] = ws1.receive_json()

        player_1 = hello_1["payload"]["players"][0]["id"]
        player_2 = joined["payload"]["player"]["id"]
        expected_first_active = min(player_1, player_2)
        non_active_ws = ws2 if expected_first_active == player_1 else ws1

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-2",
                "payload": {},
            }
        )
        ws1.receive_json()
        ws2.receive_json()

        non_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "END_TURN",
                "client_msg_id": "end-invalid",
                "payload": {},
            }
        )
        end_error: Dict[str, Any] = non_active_ws.receive_json()
        assert end_error["type"] == "ERROR"
        assert "Only active player" in end_error["payload"]["message"]

        non_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "MOVE_TOKEN",
                "client_msg_id": "move-invalid",
                "payload": {"token_id": "A", "x_mm": 200, "y_mm": 200},
            }
        )
        move_error: Dict[str, Any] = non_active_ws.receive_json()
        assert move_error["type"] == "ERROR"
        assert "MOVE_TOKEN is only allowed for active player" in move_error["payload"]["message"]

        non_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ROLL_DICE",
                "client_msg_id": "roll-invalid-active",
                "payload": {"count": 2, "sides": 6},
            }
        )
        roll_error: Dict[str, Any] = non_active_ws.receive_json()
        assert roll_error["type"] == "ERROR"
        assert "ROLL_DICE is only allowed for active player" in roll_error["payload"]["message"]

        non_active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-invalid-active",
                "payload": {"token_id": "A", "activation_type": "rest"},
            }
        )
        activate_error: Dict[str, Any] = non_active_ws.receive_json()
        assert activate_error["type"] == "ERROR"
        assert "ACTIVATE_TOKEN is only allowed for active player" in activate_error["payload"]["message"]
