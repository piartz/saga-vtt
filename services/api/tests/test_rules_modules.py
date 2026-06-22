from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import ROOMS, app

SAGA_CORE_RULES_MODULE = {"id": "saga-core", "name": "SAGA Core", "version": "0.1.0"}
SAGA_CORE_FIXTURE_IDS = {
    "unit_types": ["warlord", "hearthguards", "warriors", "levies"],
    "terrain_traits": ["open", "uneven", "dangerous", "impassable"],
    "ability_timings": [
        "orders",
        "orders-reaction",
        "activation",
        "activation-reaction",
        "shooting",
        "shooting-reaction",
        "melee",
        "melee-reaction",
    ],
    "scenarios": ["clash-of-warlords"],
}


@pytest.fixture(autouse=True)
def clear_rooms() -> None:
    ROOMS.clear()
    yield
    ROOMS.clear()


def test_list_rules_modules_includes_saga_core_module() -> None:
    client = TestClient(app)

    response = client.get("/rules/modules")

    assert response.status_code == 200
    assert response.json() == {"modules": [SAGA_CORE_RULES_MODULE]}


def test_get_rules_module_manifest_includes_saga_core_fixtures() -> None:
    client = TestClient(app)

    response = client.get("/rules/modules/saga-core")

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["id"] == "saga-core"
    assert manifest["name"] == "SAGA Core"
    assert manifest["version"] == "0.1.0"
    assert [item["id"] for item in manifest["unit_types"]] == SAGA_CORE_FIXTURE_IDS["unit_types"]
    assert [item["role"] for item in manifest["unit_types"]] == ["warlord", "hearthguards", "warriors", "levies"]
    assert {item["base_profile_id"] for item in manifest["unit_types"]} == {"standard-foot-round"}
    assert [item["generates_saga_dice_at_figures"] for item in manifest["unit_types"]] == [1, 1, 4, 6]
    assert [item["id"] for item in manifest["terrain_traits"]] == SAGA_CORE_FIXTURE_IDS["terrain_traits"]
    assert [item["id"] for item in manifest["ability_timings"]] == SAGA_CORE_FIXTURE_IDS["ability_timings"]
    assert [item["id"] for item in manifest["scenarios"]] == SAGA_CORE_FIXTURE_IDS["scenarios"]
    assert manifest["scenarios"][0]["setup_steps"] == [
        "choose_board_edge",
        "place_terrain",
        "deploy_warbands",
        "confirm_ready",
    ]
    assert manifest["scenarios"][0]["objective_ids"] == ["survival_points", "slaughtering_points"]


def test_get_rules_module_manifest_rejects_unknown_module() -> None:
    client = TestClient(app)

    response = client.get("/rules/modules/missing-module")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown rules module 'missing-module'."


def test_create_game_defaults_to_saga_core_rules_module() -> None:
    client = TestClient(app)

    response = client.post("/games")

    assert response.status_code == 200
    body = response.json()
    assert body["rules_module"] == SAGA_CORE_RULES_MODULE
    assert ROOMS[body["game_id"]].rules_module.id == "saga-core"


def test_create_game_accepts_explicit_saga_core_rules_module() -> None:
    client = TestClient(app)

    response = client.post("/games", json={"rules_module_id": "saga-core"})

    assert response.status_code == 200
    body = response.json()
    assert body["rules_module"] == SAGA_CORE_RULES_MODULE
    assert ROOMS[body["game_id"]].rules_module.id == "saga-core"


def test_create_game_rejects_unknown_rules_module() -> None:
    client = TestClient(app)

    response = client.post("/games", json={"rules_module_id": "missing-module"})

    assert response.status_code == 400
    assert "Unknown rules module 'missing-module'" in response.json()["detail"]
    assert ROOMS == {}


def test_create_game_rejects_invalid_rules_module_id_shape() -> None:
    client = TestClient(app)

    response = client.post("/games", json={"rules_module_id": ""})

    assert response.status_code == 400
    assert response.json()["detail"] == "rules_module_id must be a non-empty string."
    assert ROOMS == {}


def test_rules_module_is_included_in_hello_snapshot() -> None:
    client = TestClient(app)
    create_response = client.post("/games", json={"rules_module_id": "saga-core"})
    game_id = create_response.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws:
        hello: Dict[str, Any] = ws.receive_json()

    assert hello["type"] == "HELLO"
    assert hello["payload"]["rules_module"] == SAGA_CORE_RULES_MODULE
