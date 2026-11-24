"""Events a handler asks the transport to send."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# "sender": only the connection that sent the message; "room": every connection in the room;
# "others": every connection except the sender.
Audience = Literal["sender", "room", "others"]


@dataclass(frozen=True)
class Emit:
    """One event to send.

    Handlers return emits in order and the transport builds and sends each event in that order,
    so ``seq`` numbers are assigned exactly as they are sent.
    """

    event_type: str
    payload: dict[str, Any]
    audience: Audience
    actor_player_id: str | None = None


def error(actor_player_id: str, message: str, **details: Any) -> list[Emit]:
    """A private ERROR event for the sender."""
    return [Emit("ERROR", {"message": message, **details}, "sender", actor_player_id)]
