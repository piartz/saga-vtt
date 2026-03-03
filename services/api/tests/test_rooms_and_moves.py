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
    assert body["created"] is True


def test_create_game_returns_existing_room_for_same_client() -> None:
    client = TestClient(app)

    first_response = client.post("/games", headers={"X-Client-Id": "user-1"})
    second_response = client.post("/games", headers={"X-Client-Id": "user-1"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_body = first_response.json()
    second_body = second_response.json()
    assert first_body["game_id"] == second_body["game_id"]
    assert first_body["created"] is True
    assert second_body["created"] is False
    assert len(ROOMS) == 1


def test_create_game_creates_new_room_for_different_client() -> None:
    client = TestClient(app)

    first_response = client.post("/games", headers={"X-Client-Id": "user-1"})
    second_response = client.post("/games", headers={"X-Client-Id": "user-2"})

    first_body = first_response.json()
    second_body = second_response.json()
    assert first_body["game_id"] != second_body["game_id"]
    assert first_body["created"] is True
    assert second_body["created"] is True
    assert len(ROOMS) == 2


def test_list_rooms_excludes_rooms_without_players() -> None:
    client = TestClient(app)
    created = client.post("/games")
    created_game_id = created.json()["game_id"]

    response = client.get("/rooms")
    assert response.status_code == 200
    body = response.json()
    assert body["rooms"] == []
    assert created_game_id in ROOMS


def test_list_rooms_includes_connected_room_and_updates_player_count() -> None:
    client = TestClient(app)
    created = client.post("/games")
    game_id = created.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws1:
        ws1.receive_json()
        list_one = client.get("/rooms").json()["rooms"]
        assert list_one == [
            {
                "game_id": game_id,
                "player_count": 1,
                "phase": "lobby",
                "round": 0,
            }
        ]

        with client.websocket_connect(f"/games/{game_id}/ws") as ws2:
            ws2.receive_json()
            ws1.receive_json()
            list_two = client.get("/rooms").json()["rooms"]
            assert list_two == [
                {
                    "game_id": game_id,
                    "player_count": 2,
                    "phase": "lobby",
                    "round": 0,
                }
            ]

        ws1.receive_json()
        list_back_to_one = client.get("/rooms").json()["rooms"]
        assert list_back_to_one == [
            {
                "game_id": game_id,
                "player_count": 1,
                "phase": "lobby",
                "round": 0,
            }
        ]

    assert client.get("/rooms").json()["rooms"] == []


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
        assert player_2 in [player["id"] for player in hello_2["payload"]["players"]]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-activation-test",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        rolled_2: Dict[str, Any] = ws2.receive_json()
        assert rolled_1["type"] == "INITIATIVE_ROLLED"
        assert rolled_2["type"] == "INITIATIVE_ROLLED"
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]

        winner_ws = ws1 if winner_player_id == player_1 else ws2
        active_ws = winner_ws
        actor_player_id = winner_player_id

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-activation-order",
                "payload": {"choice": "FIRST"},
            }
        )
        ws1.receive_json()  # TURN_ORDER_CHOSEN
        ws2.receive_json()  # TURN_ORDER_CHOSEN
        ws1.receive_json()  # GAME_STARTED
        ws2.receive_json()  # GAME_STARTED

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

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        joined: Dict[str, Any] = ws1.receive_json()
        assert joined["type"] == "PLAYER_JOINED"
        player_1 = hello_1["payload"]["players"][0]["id"]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-rest-rule",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]
        winner_ws = ws1 if winner_player_id == player_1 else ws2
        active_ws = winner_ws

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-rest-order",
                "payload": {"choice": "FIRST"},
            }
        )
        ws1.receive_json()  # TURN_ORDER_CHOSEN
        ws2.receive_json()  # TURN_ORDER_CHOSEN
        ws1.receive_json()  # GAME_STARTED
        ws2.receive_json()  # GAME_STARTED

        active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-move-before-rest",
                "payload": {"token_id": "A", "activation_type": "move"},
            }
        )
        first_activation: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        assert first_activation["type"] == "TOKEN_ACTIVATED"
        assert first_activation["payload"]["token"]["activation_count_this_turn"] == 1
        assert first_activation["payload"]["token"]["last_activation_type"] == "move"

        active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-rest-after-move",
                "payload": {"token_id": "A", "activation_type": "rest"},
            }
        )
        rest_error: Dict[str, Any] = active_ws.receive_json()
        assert rest_error["type"] == "ERROR"
        assert "cannot activate to rest after prior activations this turn" in rest_error["payload"]["message"]
        assert ROOMS[game_id].tokens["A"]["activation_count_this_turn"] == 1
        assert ROOMS[game_id].tokens["A"]["last_activation_type"] == "move"

        active_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-rest-fresh-token",
                "payload": {"token_id": "B", "activation_type": "rest"},
            }
        )
        rest_ok: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
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

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-1",
                "payload": {},
            }
        )

        rolled_1: Dict[str, Any] = ws1.receive_json()
        rolled_2: Dict[str, Any] = ws2.receive_json()

        assert rolled_1["type"] == "INITIATIVE_ROLLED"
        assert rolled_2["type"] == "INITIATIVE_ROLLED"
        initiative = rolled_1["payload"]["initiative"]
        winner_player_id = initiative["winner_player_id"]
        loser_player_id = initiative["loser_player_id"]
        assert winner_player_id in (player_1, player_2)
        assert loser_player_id in (player_1, player_2)
        assert winner_player_id != loser_player_id
        assert initiative["chooser_choice"] is None
        assert initiative["first_player_id"] is None
        assert initiative["second_player_id"] is None

        winner_ws = ws1 if winner_player_id == player_1 else ws2
        loser_ws = ws2 if winner_ws is ws1 else ws1

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-1",
                "payload": {"choice": "FIRST"},
            }
        )

        chosen_1: Dict[str, Any] = ws1.receive_json()
        chosen_2: Dict[str, Any] = ws2.receive_json()
        assert chosen_1["type"] == "TURN_ORDER_CHOSEN"
        assert chosen_2["type"] == "TURN_ORDER_CHOSEN"
        assert chosen_1["payload"]["initiative"]["chooser_choice"] == "FIRST"
        assert chosen_1["payload"]["initiative"]["first_player_id"] == winner_player_id
        assert chosen_1["payload"]["initiative"]["second_player_id"] == loser_player_id

        started_1: Dict[str, Any] = ws1.receive_json()
        started_2: Dict[str, Any] = ws2.receive_json()
        assert started_1["type"] == "GAME_STARTED"
        assert started_2["type"] == "GAME_STARTED"
        assert started_1["payload"]["turn"] == {
            "phase": "running",
            "round": 1,
            "active_player_id": winner_player_id,
        }
        sorted_player_ids = sorted([player_1, player_2])
        winner_index = sorted_player_ids.index(winner_player_id)
        round_after_first_end = 2 if winner_index == 1 else 1

        first_active_ws = winner_ws
        second_active_ws = loser_ws

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
            "round": round_after_first_end,
            "active_player_id": loser_player_id,
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
            "active_player_id": winner_player_id,
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
        ws1_prefetched: Dict[str, Any] | None = None
        if hello_1["type"] != "HELLO":
            ws1_prefetched = hello_1
            hello_1 = ws1.receive_json()
        assert hello_1["type"] == "HELLO"
        hello_2: Dict[str, Any] = ws2.receive_json()
        assert hello_2["type"] == "HELLO"
        joined_event: Dict[str, Any] = ws1_prefetched if ws1_prefetched is not None else ws1.receive_json()
        assert joined_event["type"] == "PLAYER_JOINED"

        player_1 = hello_1["payload"]["players"][0]["id"]
        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-2",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]
        loser_player_id = rolled_1["payload"]["initiative"]["loser_player_id"]

        winner_ws = ws1 if winner_player_id == player_1 else ws2
        loser_ws = ws2 if winner_ws is ws1 else ws1

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-2",
                "payload": {"choice": "FIRST"},
            }
        )
        ws1.receive_json()  # TURN_ORDER_CHOSEN
        ws2.receive_json()  # TURN_ORDER_CHOSEN
        ws1.receive_json()  # GAME_STARTED
        ws2.receive_json()  # GAME_STARTED

        non_active_ws = loser_ws
        assert loser_player_id != winner_player_id

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

def test_only_initiative_winner_can_choose_turn_order() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        ws1.receive_json()

        player_1 = hello_1["payload"]["players"][0]["id"]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-3",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]
        loser_ws = ws2 if winner_player_id == player_1 else ws1

        loser_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-invalid",
                "payload": {"choice": "SECOND"},
            }
        )
        error: Dict[str, Any] = loser_ws.receive_json()
        assert error["type"] == "ERROR"
        assert "Only initiative winner can choose first or second." == error["payload"]["message"]


def test_move_undo_requires_opponent_accept_and_is_limited_to_one_per_turn() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        ws1.receive_json()
        player_1 = hello_1["payload"]["players"][0]["id"]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-undo-move",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]
        winner_ws = ws1 if winner_player_id == player_1 else ws2
        loser_ws = ws2 if winner_ws is ws1 else ws1

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-undo-move",
                "payload": {"choice": "FIRST"},
            }
        )
        ws1.receive_json()  # TURN_ORDER_CHOSEN
        ws2.receive_json()  # TURN_ORDER_CHOSEN
        ws1.receive_json()  # GAME_STARTED
        ws2.receive_json()  # GAME_STARTED

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "MOVE_TOKEN",
                "client_msg_id": "move-before-undo",
                "payload": {"token_id": "A", "x_mm": 222, "y_mm": 111},
            }
        )
        ws1.receive_json()  # TOKEN_MOVED
        ws2.receive_json()  # TOKEN_MOVED
        assert ROOMS[game_id].tokens["A"]["x_mm"] == 222
        assert ROOMS[game_id].tokens["A"]["y_mm"] == 111

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "REQUEST_UNDO",
                "client_msg_id": "undo-request-1",
                "payload": {},
            }
        )
        requested_1: Dict[str, Any] = ws1.receive_json()
        requested_2: Dict[str, Any] = ws2.receive_json()
        assert requested_1["type"] == "UNDO_REQUESTED"
        assert requested_2["type"] == "UNDO_REQUESTED"
        assert requested_1["payload"]["request"]["action_type"] == "MOVE_TOKEN"
        assert requested_1["payload"]["request"]["token_id"] == "A"

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "END_TURN",
                "client_msg_id": "end-while-undo-pending",
                "payload": {},
            }
        )
        blocked_error: Dict[str, Any] = winner_ws.receive_json()
        assert blocked_error["type"] == "ERROR"
        assert "Undo request pending" in blocked_error["payload"]["message"]

        loser_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "RESPOND_UNDO_REQUEST",
                "client_msg_id": "undo-accept-1",
                "payload": {"accept": True},
            }
        )
        applied_1: Dict[str, Any] = ws1.receive_json()
        applied_2: Dict[str, Any] = ws2.receive_json()
        assert applied_1["type"] == "UNDO_APPLIED"
        assert applied_2["type"] == "UNDO_APPLIED"
        assert applied_1["payload"]["token"]["id"] == "A"
        assert applied_1["payload"]["token"]["x_mm"] == 160
        assert applied_1["payload"]["token"]["y_mm"] == 140
        assert ROOMS[game_id].tokens["A"]["x_mm"] == 160
        assert ROOMS[game_id].tokens["A"]["y_mm"] == 140

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "MOVE_TOKEN",
                "client_msg_id": "move-after-undo",
                "payload": {"token_id": "A", "x_mm": 210, "y_mm": 120},
            }
        )
        ws1.receive_json()  # TOKEN_MOVED
        ws2.receive_json()  # TOKEN_MOVED

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "REQUEST_UNDO",
                "client_msg_id": "undo-request-2",
                "payload": {},
            }
        )
        undo_limit_error: Dict[str, Any] = winner_ws.receive_json()
        assert undo_limit_error["type"] == "ERROR"
        assert "already used your undo request this turn" in undo_limit_error["payload"]["message"]


def test_activation_undo_can_be_rejected_and_state_stays_unchanged() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        ws1.receive_json()  # PLAYER_JOINED
        player_1 = hello_1["payload"]["players"][0]["id"]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-undo-activation",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]
        winner_ws = ws1 if winner_player_id == player_1 else ws2
        loser_ws = ws2 if winner_ws is ws1 else ws1

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-undo-activation",
                "payload": {"choice": "FIRST"},
            }
        )
        ws1.receive_json()  # TURN_ORDER_CHOSEN
        ws2.receive_json()  # TURN_ORDER_CHOSEN
        ws1.receive_json()  # GAME_STARTED
        ws2.receive_json()  # GAME_STARTED

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ACTIVATE_TOKEN",
                "client_msg_id": "activate-before-undo",
                "payload": {"token_id": "A", "activation_type": "rest"},
            }
        )
        ws1.receive_json()  # TOKEN_ACTIVATED
        ws2.receive_json()  # TOKEN_ACTIVATED
        assert ROOMS[game_id].tokens["A"]["activation_count_this_turn"] == 1
        assert ROOMS[game_id].tokens["A"]["last_activation_type"] == "rest"

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "REQUEST_UNDO",
                "client_msg_id": "undo-request-activation",
                "payload": {},
            }
        )
        ws1.receive_json()  # UNDO_REQUESTED
        ws2.receive_json()  # UNDO_REQUESTED

        loser_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "RESPOND_UNDO_REQUEST",
                "client_msg_id": "undo-reject-activation",
                "payload": {"accept": False},
            }
        )
        rejected_1: Dict[str, Any] = ws1.receive_json()
        rejected_2: Dict[str, Any] = ws2.receive_json()
        assert rejected_1["type"] == "UNDO_REJECTED"
        assert rejected_2["type"] == "UNDO_REJECTED"
        assert ROOMS[game_id].tokens["A"]["activation_count_this_turn"] == 1
        assert ROOMS[game_id].tokens["A"]["last_activation_type"] == "rest"

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "REQUEST_UNDO",
                "client_msg_id": "undo-request-activation-2",
                "payload": {},
            }
        )
        undo_limit_error: Dict[str, Any] = winner_ws.receive_json()
        assert undo_limit_error["type"] == "ERROR"
        assert "already used your undo request this turn" in undo_limit_error["payload"]["message"]


def test_non_board_actions_cannot_be_undone() -> None:
    client = TestClient(app)
    create_response = client.post("/games")
    game_id = create_response.json()["game_id"]

    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        hello_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        ws1.receive_json()  # PLAYER_JOINED
        player_1 = hello_1["payload"]["players"][0]["id"]

        ws1.send_json(
            {
                "kind": "COMMAND",
                "type": "START_GAME",
                "client_msg_id": "start-undo-non-board",
                "payload": {},
            }
        )
        rolled_1: Dict[str, Any] = ws1.receive_json()
        ws2.receive_json()
        winner_player_id = rolled_1["payload"]["initiative"]["winner_player_id"]
        winner_ws = ws1 if winner_player_id == player_1 else ws2

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "CHOOSE_TURN_ORDER",
                "client_msg_id": "choose-undo-non-board",
                "payload": {"choice": "FIRST"},
            }
        )
        ws1.receive_json()  # TURN_ORDER_CHOSEN
        ws2.receive_json()  # TURN_ORDER_CHOSEN
        ws1.receive_json()  # GAME_STARTED
        ws2.receive_json()  # GAME_STARTED

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "ROLL_DICE",
                "client_msg_id": "roll-before-undo",
                "payload": {"count": 1, "sides": 6},
            }
        )
        ws1.receive_json()  # DICE_ROLLED
        ws2.receive_json()  # DICE_ROLLED

        winner_ws.send_json(
            {
                "kind": "COMMAND",
                "type": "REQUEST_UNDO",
                "client_msg_id": "undo-request-non-board",
                "payload": {},
            }
        )
        undo_error: Dict[str, Any] = winner_ws.receive_json()
        assert undo_error["type"] == "ERROR"
        assert "No board action to undo this turn." == undo_error["payload"]["message"]
