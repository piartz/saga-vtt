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
                "id": "warlord",
                "name": "Warlord",
                "role": "hero",
                "min_figures": 1,
                "max_figures": 1,
                "base_profile_id": "single-round",
                "generates_command_resource_at_figures": 1,
            },
            {
                "id": "hearthguards",
                "name": "Hearthguards",
                "role": "elite",
                "min_figures": 4,
                "max_figures": 12,
                "base_profile_id": "small-round",
                "generates_command_resource_at_figures": 1,
            },
            {
                "id": "warriors",
                "name": "Warriors",
                "role": "core",
                "min_figures": 4,
                "max_figures": 12,
                "base_profile_id": "small-round",
                "generates_command_resource_at_figures": 4,
            },
            {
                "id": "levies",
                "name": "Levies",
                "role": "levy",
                "min_figures": 4,
                "max_figures": 12,
                "base_profile_id": "small-round",
                "generates_command_resource_at_figures": 6,
            },
        ),
        terrain_traits=(
            {
                "id": "open",
                "name": "Open Terrain",
                "movement_effect": "none",
                "cover_effect": "none",
                "blocks_line_of_sight": False,
                "adds_fatigue_on_entry": False,
            },
            {
                "id": "uneven",
                "name": "Uneven Terrain",
                "movement_effect": "slow",
                "cover_effect": "light",
                "blocks_line_of_sight": False,
                "adds_fatigue_on_entry": False,
            },
            {
                "id": "dangerous",
                "name": "Dangerous Terrain",
                "movement_effect": "slow",
                "cover_effect": "none",
                "blocks_line_of_sight": False,
                "adds_fatigue_on_entry": True,
            },
            {
                "id": "impassable",
                "name": "Impassable Terrain",
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
                "phase": "orders",
                "trigger_window": "active_player_orders",
                "repeatable_per_turn": False,
            },
            {
                "id": "orders-reaction",
                "name": "Orders/Reaction",
                "phase": "orders",
                "trigger_window": "opponent_orders_window",
                "repeatable_per_turn": False,
            },
            {
                "id": "activation",
                "name": "Activation",
                "phase": "activation",
                "trigger_window": "active_player_activation",
                "repeatable_per_turn": True,
            },
            {
                "id": "activation-reaction",
                "name": "Activation/Reaction",
                "phase": "activation",
                "trigger_window": "opponent_activation_window",
                "repeatable_per_turn": False,
            },
            {
                "id": "shooting",
                "name": "Shooting",
                "phase": "shooting",
                "trigger_window": "during_shooting",
                "repeatable_per_turn": False,
            },
            {
                "id": "shooting-reaction",
                "name": "Shooting/Reaction",
                "phase": "shooting",
                "trigger_window": "opponent_shooting_window",
                "repeatable_per_turn": False,
            },
            {
                "id": "melee",
                "name": "Melee",
                "phase": "melee",
                "trigger_window": "during_melee",
                "repeatable_per_turn": False,
            },
            {
                "id": "melee-reaction",
                "name": "Melee/Reaction",
                "phase": "melee",
                "trigger_window": "opponent_melee_window",
                "repeatable_per_turn": False,
            },
        ),
        scenarios=(
            {
                "id": "clash-of-warlords",
                "name": "Clash of Warlords",
                "board_width_mm": 800,
                "board_height_mm": 500,
                "setup_steps": [
                    "choose_board_edge",
                    "place_terrain",
                    "deploy_warbands",
                    "confirm_ready",
                ],
                "turn_limit": 6,
                "objective_ids": ["score_survival", "score_enemy_losses"],
            },
        ),
    )


TOY_SKIRMISH_MODULE = ToySkirmishModule()
