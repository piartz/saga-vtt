from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, TypedDict


class RulesModuleSnapshot(TypedDict):
    id: str
    name: str
    version: str


class UnitTypeDefinition(TypedDict):
    id: str
    name: str
    role: str
    min_figures: int
    max_figures: int
    base_profile_id: str
    generates_saga_dice_at_figures: int | None


class TerrainTraitDefinition(TypedDict):
    id: str
    name: str
    movement_effect: str
    cover_effect: str
    blocks_line_of_sight: bool
    adds_fatigue_on_entry: bool


class AbilityTimingDefinition(TypedDict):
    id: str
    name: str
    phase: str
    trigger_window: str
    repeatable_per_turn: bool


class ScenarioDefinition(TypedDict):
    id: str
    name: str
    board_width_mm: int
    board_height_mm: int
    setup_steps: list[str]
    turn_limit: int | None
    objective_ids: list[str]


class RulesModuleManifest(TypedDict):
    id: str
    name: str
    version: str
    unit_types: list[UnitTypeDefinition]
    terrain_traits: list[TerrainTraitDefinition]
    ability_timings: list[AbilityTimingDefinition]
    scenarios: list[ScenarioDefinition]


@dataclass(frozen=True)
class RulesModule:
    id: str
    name: str
    version: str
    unit_types: tuple[UnitTypeDefinition, ...] = field(default_factory=tuple)
    terrain_traits: tuple[TerrainTraitDefinition, ...] = field(default_factory=tuple)
    ability_timings: tuple[AbilityTimingDefinition, ...] = field(default_factory=tuple)
    scenarios: tuple[ScenarioDefinition, ...] = field(default_factory=tuple)

    def snapshot(self) -> RulesModuleSnapshot:
        return {"id": self.id, "name": self.name, "version": self.version}

    def manifest(self) -> RulesModuleManifest:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "unit_types": list(self.unit_types),
            "terrain_traits": list(self.terrain_traits),
            "ability_timings": list(self.ability_timings),
            "scenarios": list(self.scenarios),
        }


class RulesModuleProvider(Protocol):
    @property
    def metadata(self) -> RulesModule:
        """Return stable public metadata for this rules module."""
