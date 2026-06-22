from __future__ import annotations

from dataclasses import dataclass

from app.rules.types import RulesModule


@dataclass(frozen=True)
class ToySkirmishModule:
    metadata: RulesModule = RulesModule(
        id="toy-skirmish",
        name="Toy Skirmish",
        version="0.1.0",
    )


TOY_SKIRMISH_MODULE = ToySkirmishModule()
