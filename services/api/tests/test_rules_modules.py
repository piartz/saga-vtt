from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import ROOMS, app

TOY_RULES_MODULE = {"id": "toy-skirmish", "name": "Toy Skirmish", "version": "0.1.0"}
TOY_FIXTURE_IDS = {
    "unit_types": ["captain", "sentinel", "runner"],
    "terrain_traits": ["clear", "rough", "hazard", "obstruction"],
    "ability_timings": ["orders", "activation", "reaction", "combat"],
    "scenarios": ["training-field"],
}


@pytest.fixture(autouse=True)
def clear_rooms() -> None:
    ROOMS.clear()
    yield
    ROOMS.clear()


def test_list_rules_modules_includes_toy_module() -> None:
    client = TestClient(app)

    response = client.get("/rules/modules")

    assert response.status_code == 200
    assert response.json() == {"modules": [TOY_RULES_MODULE]}


def test_get_rules_module_manifest_includes_original_toy_fixtures() -> None:
    client = TestClient(app)

    response = client.get("/rules/modules/toy-skirmish")

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["id"] == "toy-skirmish"
    assert manifest["name"] == "Toy Skirmish"
    assert manifest["version"] == "0.1.0"
    assert [item["id"] for item in manifest["unit_types"]] == TOY_FIXTURE_IDS["unit_types"]
    assert [item["id"] for item in manifest["terrain_traits"]] == TOY_FIXTURE_IDS["terrain_traits"]
    assert [item["id"] for item in manifest["ability_timings"]] == TOY_FIXTURE_IDS["ability_timings"]
    assert [item["id"] for item in manifest["scenarios"]] == TOY_FIXTURE_IDS["scenarios"]
    assert manifest["scenarios"][0]["setup_steps"] == [
        "choose_sides",
        "place_terrain",
        "deploy_units",
        "confirm_ready",
    ]


def test_get_rules_module_manifest_rejects_unknown_module() -> None:
    client = TestClient(app)

    response = client.get("/rules/modules/missing-module")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown rules module 'missing-module'."


def test_create_game_defaults_to_toy_rules_module() -> None:
    client = TestClient(app)

    response = client.post("/games")

    assert response.status_code == 200
    body = response.json()
    assert body["rules_module"] == TOY_RULES_MODULE
    assert ROOMS[body["game_id"]].rules_module.id == "toy-skirmish"


def test_create_game_accepts_explicit_toy_rules_module() -> None:
    client = TestClient(app)

    response = client.post("/games", json={"rules_module_id": "toy-skirmish"})

    assert response.status_code == 200
    body = response.json()
    assert body["rules_module"] == TOY_RULES_MODULE
    assert ROOMS[body["game_id"]].rules_module.id == "toy-skirmish"


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
    create_response = client.post("/games", json={"rules_module_id": "toy-skirmish"})
    game_id = create_response.json()["game_id"]

    with client.websocket_connect(f"/games/{game_id}/ws") as ws:
        hello: Dict[str, Any] = ws.receive_json()

    assert hello["type"] == "HELLO"
    assert hello["payload"]["rules_module"] == TOY_RULES_MODULE
