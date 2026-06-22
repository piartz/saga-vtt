from __future__ import annotations

from dataclasses import dataclass

from app.rules.types import RulesModule


@dataclass(frozen=True)
class ToySkirmishModule:
    metadata: RulesModule = RulesModule(
        id="toy-skirmish",
        name="Toy Skirmish",
        version="0.1.0",
        unit_types=(
            {
                "id": "captain",
                "name": "Captain",
                "role": "leader",
                "min_figures": 1,
                "max_figures": 1,
                "base_profile_id": "single-round",
                "generates_command_resource_at_figures": 1,
            },
            {
                "id": "sentinel",
                "name": "Sentinel",
                "role": "trained",
                "min_figures": 4,
                "max_figures": 12,
                "base_profile_id": "small-round",
                "generates_command_resource_at_figures": 1,
            },
            {
                "id": "runner",
                "name": "Runner",
                "role": "support",
                "min_figures": 4,
                "max_figures": 12,
                "base_profile_id": "small-round",
                "generates_command_resource_at_figures": 6,
            },
        ),
        terrain_traits=(
            {
                "id": "clear",
                "name": "Clear Ground",
                "movement_effect": "none",
                "cover_effect": "none",
                "blocks_line_of_sight": False,
                "adds_fatigue_on_entry": False,
            },
            {
                "id": "rough",
                "name": "Rough Ground",
                "movement_effect": "slow",
                "cover_effect": "light",
                "blocks_line_of_sight": False,
                "adds_fatigue_on_entry": False,
            },
            {
                "id": "hazard",
                "name": "Hazard",
                "movement_effect": "slow",
                "cover_effect": "none",
                "blocks_line_of_sight": False,
                "adds_fatigue_on_entry": True,
            },
            {
                "id": "obstruction",
                "name": "Obstruction",
                "movement_effect": "blocked",
                "cover_effect": "solid",
                "blocks_line_of_sight": True,
                "adds_fatigue_on_entry": False,
            },
        ),
        ability_timings=(
            {
                "id": "orders",
                "name": "Orders",
                "phase": "planning",
                "trigger_window": "active_player_planning",
                "repeatable_per_turn": False,
            },
            {
                "id": "activation",
                "name": "Activation",
                "phase": "activation",
                "trigger_window": "before_unit_action",
                "repeatable_per_turn": True,
            },
            {
                "id": "reaction",
                "name": "Reaction",
                "phase": "any",
                "trigger_window": "opponent_action_window",
                "repeatable_per_turn": False,
            },
            {
                "id": "combat",
                "name": "Combat",
                "phase": "combat",
                "trigger_window": "during_combat_resolution",
                "repeatable_per_turn": False,
            },
        ),
        scenarios=(
            {
                "id": "training-field",
                "name": "Training Field",
                "board_width_mm": 800,
                "board_height_mm": 500,
                "setup_steps": ["choose_sides", "place_terrain", "deploy_units", "confirm_ready"],
                "turn_limit": 6,
                "objective_ids": ["hold_center", "preserve_leader"],
            },
        ),
    )


TOY_SKIRMISH_MODULE = ToySkirmishModule()
