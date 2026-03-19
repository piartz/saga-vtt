"""
Integration smoke test: validates minimal complete game flow.

This test exercises the core game loop from room creation through
a complete turn cycle, ensuring all major systems work together.
"""
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import ROOMS, app


@pytest.fixture(autouse=True)
def clear_rooms() -> None:
    ROOMS.clear()
    yield
    ROOMS.clear()


def test_complete_game_flow_smoke() -> None:
    """
    Integration smoke test: complete game session flow.

    Flow:
    1. Create room
    2. Two players connect
    3. Start game (initiative roll)
    4. Winner chooses turn order
    5. First player moves token
    6. First player activates token
    7. First player ends turn
    8. Second player moves token
    9. Second player ends turn (round advances)
    10. Verify game state progression
    """
    client = TestClient(app)

    # Step 1: Create room
    create_response = client.post("/games")
    assert create_response.status_code == 200
    game_id = create_response.json()["game_id"]
    assert game_id in ROOMS

    # Step 2: Two players connect
    with (
        client.websocket_connect(f"/games/{game_id}/ws") as ws1,
        client.websocket_connect(f"/games/{game_id}/ws") as ws2,
    ):
        # Player 1 receives HELLO
        hello_1: Dict[str, Any] = ws1.receive_json()
        assert hello_1["type"] == "HELLO"
        assert hello_1["payload"]["turn"]["phase"] == "lobby"
        assert hello_1["payload"]["turn"]["round"] == 0
        player_1_id = hello_1["payload"]["self_player_id"]

        # Player 2 receives HELLO
        hello_2: Dict[str, Any] = ws2.receive_json()
        assert hello_2["type"] == "HELLO"
        assert hello_2["payload"]["turn"]["phase"] == "lobby"
        player_2_id = hello_2["payload"]["self_player_id"]

        # Player 1 receives PLAYER_JOINED for player 2
        joined: Dict[str, Any] = ws1.receive_json()
        assert joined["type"] == "PLAYER_JOINED"
        assert joined["payload"]["player"]["id"] == player_2_id

        # Step 3: Start game (initiative roll)
        ws1.send_json({
            "kind": "COMMAND",
            "type": "START_GAME",
            "client_msg_id": "smoke-start",
            "payload": {},
        })

        rolled_1: Dict[str, Any] = ws1.receive_json()
        rolled_2: Dict[str, Any] = ws2.receive_json()
        assert rolled_1["type"] == "INITIATIVE_ROLLED"
        assert rolled_2["type"] == "INITIATIVE_ROLLED"

        initiative = rolled_1["payload"]["initiative"]
        winner_id = initiative["winner_player_id"]
        loser_id = initiative["loser_player_id"]
        assert winner_id in (player_1_id, player_2_id)
        assert loser_id in (player_1_id, player_2_id)
        assert winner_id != loser_id

        # Step 4: Winner chooses turn order
        winner_ws = ws1 if winner_id == player_1_id else ws2

        winner_ws.send_json({
            "kind": "COMMAND",
            "type": "CHOOSE_TURN_ORDER",
            "client_msg_id": "smoke-choose",
            "payload": {"choice": "FIRST"},
        })

        chosen_1: Dict[str, Any] = ws1.receive_json()
        chosen_2: Dict[str, Any] = ws2.receive_json()
        assert chosen_1["type"] == "TURN_ORDER_CHOSEN"
        assert chosen_2["type"] == "TURN_ORDER_CHOSEN"
        assert chosen_1["payload"]["initiative"]["first_player_id"] == winner_id
        assert chosen_1["payload"]["initiative"]["second_player_id"] == loser_id

        started_1: Dict[str, Any] = ws1.receive_json()
        started_2: Dict[str, Any] = ws2.receive_json()
        assert started_1["type"] == "GAME_STARTED"
        assert started_2["type"] == "GAME_STARTED"
        assert started_1["payload"]["turn"]["phase"] == "running"
        assert started_1["payload"]["turn"]["round"] == 1
        assert started_1["payload"]["turn"]["active_player_id"] == winner_id

        # Step 5: First player (winner) moves token
        first_player_ws = winner_ws

        first_player_ws.send_json({
            "kind": "COMMAND",
            "type": "MOVE_TOKEN",
            "client_msg_id": "smoke-move-1",
            "payload": {"token_id": "A", "x_mm": 300, "y_mm": 200},
        })

        moved_1: Dict[str, Any] = ws1.receive_json()
        moved_2: Dict[str, Any] = ws2.receive_json()
        assert moved_1["type"] == "TOKEN_MOVED"
        assert moved_2["type"] == "TOKEN_MOVED"
        assert moved_1["payload"]["token"]["x_mm"] == 300
        assert moved_1["payload"]["token"]["y_mm"] == 200
        assert moved_1["actor_player_id"] == winner_id

        # Step 6: First player activates token
        first_player_ws.send_json({
            "kind": "COMMAND",
            "type": "ACTIVATE_TOKEN",
            "client_msg_id": "smoke-activate-1",
            "payload": {"token_id": "A", "activation_type": "move"},
        })

        activated_1: Dict[str, Any] = ws1.receive_json()
        activated_2: Dict[str, Any] = ws2.receive_json()
        assert activated_1["type"] == "TOKEN_ACTIVATED"
        assert activated_2["type"] == "TOKEN_ACTIVATED"
        assert activated_1["payload"]["token"]["activation_count_this_turn"] == 1
        assert activated_1["payload"]["token"]["last_activation_type"] == "move"

        # Step 7: First player ends turn
        first_player_ws.send_json({
            "kind": "COMMAND",
            "type": "END_TURN",
            "client_msg_id": "smoke-end-1",
            "payload": {},
        })

        turn_changed_1: Dict[str, Any] = ws1.receive_json()
        turn_changed_2: Dict[str, Any] = ws2.receive_json()
        assert turn_changed_1["type"] == "TURN_CHANGED"
        assert turn_changed_2["type"] == "TURN_CHANGED"
        assert turn_changed_1["payload"]["turn"]["active_player_id"] == loser_id

        # Verify token activations were reset
        tokens_after_turn_1 = turn_changed_1["payload"]["tokens"]
        token_a = next(t for t in tokens_after_turn_1 if t["id"] == "A")
        assert token_a["activation_count_this_turn"] == 0
        assert token_a["last_activation_type"] is None

        # Step 8: Second player (loser) moves token
        second_player_ws = ws2 if winner_ws is ws1 else ws1

        second_player_ws.send_json({
            "kind": "COMMAND",
            "type": "MOVE_TOKEN",
            "client_msg_id": "smoke-move-2",
            "payload": {"token_id": "B", "x_mm": 400, "y_mm": 300},
        })

        moved_3: Dict[str, Any] = ws1.receive_json()
        moved_4: Dict[str, Any] = ws2.receive_json()
        assert moved_3["type"] == "TOKEN_MOVED"
        assert moved_4["type"] == "TOKEN_MOVED"
        assert moved_3["payload"]["token"]["id"] == "B"
        assert moved_3["payload"]["token"]["x_mm"] == 400
        assert moved_3["actor_player_id"] == loser_id

        # Step 9: Second player ends turn (round advances)
        second_player_ws.send_json({
            "kind": "COMMAND",
            "type": "END_TURN",
            "client_msg_id": "smoke-end-2",
            "payload": {},
        })

        turn_changed_3: Dict[str, Any] = ws1.receive_json()
        turn_changed_4: Dict[str, Any] = ws2.receive_json()
        assert turn_changed_3["type"] == "TURN_CHANGED"
        assert turn_changed_4["type"] == "TURN_CHANGED"

        # Step 10: Verify game state progression
        final_turn = turn_changed_3["payload"]["turn"]
        assert final_turn["phase"] == "running"
        assert final_turn["round"] == 2  # Round advances when turn wraps
        assert final_turn["active_player_id"] == winner_id  # Back to first player

        # Verify room state is consistent
        assert ROOMS[game_id].phase == "running"
        assert ROOMS[game_id].round == 2
        assert ROOMS[game_id].active_player_id == winner_id
        assert ROOMS[game_id].tokens["A"]["x_mm"] == 300
        assert ROOMS[game_id].tokens["A"]["y_mm"] == 200
        assert ROOMS[game_id].tokens["B"]["x_mm"] == 400
        assert ROOMS[game_id].tokens["B"]["y_mm"] == 300
