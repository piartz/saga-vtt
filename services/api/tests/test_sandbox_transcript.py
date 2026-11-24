"""Golden transcript of the sandbox websocket protocol.

Replays one scripted two-player session covering every command branch, the join/leave policies,
and undo cancellation, and compares every event each client receives (type, seq, actor, and
payload; server_time removed) with ``fixtures/sandbox_transcript.json``.

Intentional protocol changes must regenerate the fixture and explain the diff:

    UPDATE_SANDBOX_TRANSCRIPT=1 poetry run pytest tests/test_sandbox_transcript.py
"""

from __future__ import annotations

import itertools
import json
import os
import secrets
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from app.main import ROOMS, app

FIXTURE = Path(__file__).parent / "fixtures" / "sandbox_transcript.json"
GAME_PATH = "/games/transcript/ws"

# Values returned by secrets.randbelow, in call order: one lobby dice roll, three initiative
# roll-offs (the first with a tie), and one in-game dice roll.
SCRIPTED_RANDBELOW = [2, 5, 9, 9, 2, 15, 11, 4, 6, 13, 19]


@pytest.fixture(autouse=True)
def clear_rooms() -> Iterator[None]:
    ROOMS.clear()
    yield
    ROOMS.clear()


class Session:
    """Drives named websocket clients and records what each one receives."""

    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.sockets: dict[str, WebSocketTestSession] = {}
        self.stacks: dict[str, ExitStack] = {}
        self.received: dict[str, list[dict[str, Any]]] = {}
        self.markers = itertools.count(1)

    def connect(self, name: str) -> None:
        inner = ExitStack()
        self.sockets[name] = inner.enter_context(self.client.websocket_connect(GAME_PATH))
        self.stacks[name] = inner
        self.received[name] = []
        self.sync(name)

    def disconnect(self, name: str) -> None:
        """Close a client and wait until the server has finished its disconnect handling.

        The test client cancels the server task right after sending the close, which would
        cut the handler's cleanup short; a real server runs it to completion.
        """
        departed = self.received[name][0]["payload"]["self_player_id"]
        self.sockets.pop(name).close(1000)
        if self.sockets:
            for other in self.sockets:
                self._read_until(
                    other,
                    lambda e: e["type"] == "PLAYER_LEFT" and e["payload"]["player_id"] == departed,
                )
        else:
            deadline = time.monotonic() + 5
            while "transcript" in ROOMS:
                assert time.monotonic() < deadline, "room was not cleaned up"
                time.sleep(0.01)
        self.stacks.pop(name).close()
        self.sync()

    def send(self, name: str, command_type: str, payload: Any = None, **extra: Any) -> None:
        message: dict[str, Any] = {"kind": "COMMAND", "type": command_type, **extra}
        if payload is not None:
            message["payload"] = payload
        self.send_raw(name, json.dumps(message))

    def send_raw(self, name: str, text: str) -> None:
        self.sockets[name].send_text(text)
        self.sync(name)

    def sync(self, sender: str | None = None) -> None:
        """Broadcast a marked PING and read every client up to its PONG.

        Each socket's messages are handled in order, so a PING from the client that sent the
        previous command is answered only after that command's events have all been sent.
        """
        if not self.sockets:
            return
        marker = next(self.markers)
        sender = sender or next(iter(self.sockets))
        self.sockets[sender].send_text(
            json.dumps({"kind": "COMMAND", "type": "PING", "payload": {"marker": marker}})
        )
        for name in self.sockets:
            self._read_until(
                name, lambda e: e["type"] == "PONG" and e["payload"]["echo"] == {"marker": marker}
            )

    def _read_until(self, name: str, is_last: Callable[[dict[str, Any]], bool]) -> None:
        while True:
            event = self.sockets[name].receive_json()
            event.pop("server_time", None)
            self.received[name].append(event)
            if is_last(event):
                return


def _play_session(session: Session) -> None:
    move = "MOVE_TOKEN"
    activate = "ACTIVATE_TOKEN"

    # Lobby: join, envelope errors, permissive lobby commands.
    session.connect("A")
    session.connect("B")
    session.send("A", "PING")
    session.send_raw("A", "not json")
    session.send_raw("A", json.dumps({"kind": "EVENT", "type": "PING"}))
    session.send("A", "NOT_A_COMMAND")
    session.send_raw("A", json.dumps({"kind": "COMMAND", "type": ["PING"]}))
    session.send("A", move, {"token_id": "A", "x_mm": 60, "y_mm": 70}, client_msg_id="m1")
    session.send("A", "ROLL_DICE", {"count": 0, "sides": 6})
    session.send("A", "ROLL_DICE", {"count": 2, "sides": 6, "modifier": -1}, client_msg_id="r1")
    session.send("A", "CHOOSE_TURN_ORDER", {"choice": "FIRST"})

    # Initiative with a tie, reset by a joining player and by a leaving participant.
    session.send("A", "START_GAME")
    session.connect("C")
    session.disconnect("C")
    session.send("A", "START_GAME")
    session.disconnect("B")
    session.connect("B2")
    session.send("A", "START_GAME")
    session.send("A", "CHOOSE_TURN_ORDER", {"choice": "FIRST"})
    session.send("A", "START_GAME")
    session.send("B2", "CHOOSE_TURN_ORDER", {"choice": "SECOND"})

    # Running game: active-player checks, activations, moves, dice.
    session.send("B2", move, {"token_id": "B", "x_mm": 100, "y_mm": 100})
    session.send("A", activate, {"token_id": "A", "activation_type": "rest"}, client_msg_id="a1")
    session.send("A", activate, {"token_id": "A", "activation_type": "rest"})
    session.send("A", activate, {"token_id": "A", "activation_type": "move"}, client_msg_id="a2")
    session.send("A", move, {"token_id": "A", "x_mm": 100, "y_mm": 120}, client_msg_id="m2")
    session.send("A", move, {"token_id": "A", "x_mm": 5, "y_mm": 5})
    session.send("A", "ROLL_DICE", {"count": 1, "sides": 20}, client_msg_id="r2")

    # Undo: request, blocked commands, accept, one request per turn.
    session.send("A", "REQUEST_UNDO")
    session.send("A", move, {"token_id": "A", "x_mm": 110, "y_mm": 120})
    session.send("B2", "ROLL_DICE", {"count": 1, "sides": 6})
    session.send("B2", "END_TURN")
    session.send("B2", "RESPOND_UNDO_REQUEST", {"accept": True})
    session.send("A", "REQUEST_UNDO")
    session.send("A", "END_TURN")

    # Second player's turn: reject an undo, then advance the round.
    session.send("B2", activate, {"token_id": "B", "activation_type": "charge"}, client_msg_id="a3")
    session.send("B2", "REQUEST_UNDO")
    session.send("A", "RESPOND_UNDO_REQUEST", {"accept": "yes"})
    session.send("A", "RESPOND_UNDO_REQUEST", {"accept": False})
    session.send("B2", "END_TURN")

    # Disconnect policies: undo cancellation, then the active player's turn is passed.
    session.send("A", move, {"token_id": "A", "x_mm": 200, "y_mm": 200}, client_msg_id="m3")
    session.send("A", "REQUEST_UNDO")
    session.disconnect("B2")
    session.send("A", "RESPOND_UNDO_REQUEST", {"accept": True})
    session.connect("B3")
    session.send("A", "END_TURN")
    session.disconnect("B3")
    session.send("A", "END_TURN")
    session.disconnect("A")


def _record(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[dict[str, Any]]]:
    token_counter = itertools.count(1)
    monkeypatch.setattr(secrets, "token_hex", lambda n=16: f"{next(token_counter):0{2 * n}x}")
    rolls = iter(SCRIPTED_RANDBELOW)

    def scripted_randbelow(upper: int) -> int:
        value = next(rolls)
        assert 0 <= value < upper
        return value

    monkeypatch.setattr(secrets, "randbelow", scripted_randbelow)

    session = Session(TestClient(app))
    try:
        _play_session(session)
    finally:
        for stack in session.stacks.values():
            stack.close()

    assert next(rolls, None) is None, "every scripted roll must be consumed"
    assert "transcript" not in ROOMS, "the room is removed when the last player leaves"
    return session.received


def _dump(transcript: dict[str, list[dict[str, Any]]]) -> str:
    blocks = []
    for name, events in transcript.items():
        lines = ",\n".join(f"    {json.dumps(event, sort_keys=True)}" for event in events)
        blocks.append(f"  {json.dumps(name)}: [\n{lines}\n  ]")
    return "{\n" + ",\n".join(blocks) + "\n}\n"


def test_sandbox_transcript_matches_golden_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _record(monkeypatch)

    if os.environ.get("UPDATE_SANDBOX_TRANSCRIPT") == "1":
        FIXTURE.parent.mkdir(exist_ok=True)
        FIXTURE.write_text(_dump(transcript), encoding="utf-8")

    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert list(transcript) == list(expected)
    for name in expected:
        assert transcript[name] == expected[name], f"transcript differs for client {name}"
