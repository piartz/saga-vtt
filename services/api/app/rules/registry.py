from __future__ import annotations

from app.rules.toy import TOY_SKIRMISH_MODULE
from app.rules.types import RulesModule

DEFAULT_RULES_MODULE_ID = TOY_SKIRMISH_MODULE.metadata.id

_RULES_MODULES: dict[str, RulesModule] = {
    TOY_SKIRMISH_MODULE.metadata.id: TOY_SKIRMISH_MODULE.metadata,
}


def get_rules_module(module_id: str) -> RulesModule | None:
    return _RULES_MODULES.get(module_id)


def require_rules_module(module_id: str) -> RulesModule:
    module = get_rules_module(module_id)
    if module is None:
        available = ", ".join(sorted(_RULES_MODULES))
        raise ValueError(f"Unknown rules module '{module_id}'. Available modules: {available}.")
    return module


def list_rules_modules() -> list[RulesModule]:
    return sorted(_RULES_MODULES.values(), key=lambda module: module.id)
