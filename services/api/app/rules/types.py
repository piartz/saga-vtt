from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict


class RulesModuleSnapshot(TypedDict):
    id: str
    name: str
    version: str


@dataclass(frozen=True)
class RulesModule:
    id: str
    name: str
    version: str

    def snapshot(self) -> RulesModuleSnapshot:
        return {"id": self.id, "name": self.name, "version": self.version}


class RulesModuleProvider(Protocol):
    @property
    def metadata(self) -> RulesModule:
        """Return stable public metadata for this rules module."""
