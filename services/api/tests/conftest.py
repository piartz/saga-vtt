from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A test client whose connections all share one event loop.

    Entered as a context manager, the client runs every websocket session on a single event
    loop, as a real server does. Without it each websocket gets its own loop thread, and a
    broadcast across loops can occasionally lose a wake-up and hang the test.
    """
    with TestClient(app) as test_client:
        yield test_client
