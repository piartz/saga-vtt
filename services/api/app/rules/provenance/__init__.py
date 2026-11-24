"""Source, requirement, decision, and work-package registry for the SAGA engine plan.

The JSON files in ``data/`` are the machine-readable index of ``rules-roadmap/``. They are
validated on load; see ``rules-roadmap/iteration-playbook.md`` for when to update them.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

from app.rules.provenance.models import (
    Conventions,
    Decision,
    Registry,
    Requirement,
    Source,
    SourceRef,
    WorkPackage,
)

DATA_DIR = Path(__file__).parent / "data"
DATA_FILES = {
    "sources": "sources.json",
    "requirements": "requirements.json",
    "decisions": "decisions.json",
    "work_packages": "work_packages.json",
    "conventions": "conventions.json",
}


def read_registry_data(data_dir: Path = DATA_DIR) -> dict[str, object]:
    """Read the raw registry JSON documents keyed by registry field."""
    return {
        field: json.loads((data_dir / filename).read_text(encoding="utf-8"))
        for field, filename in DATA_FILES.items()
    }


def parse_registry(data: Mapping[str, object]) -> Registry:
    """Validate raw registry data with JSON semantics, including all cross-references."""
    return Registry.model_validate_json(json.dumps(data))


@lru_cache(maxsize=1)
def load_registry() -> Registry:
    return parse_registry(read_registry_data())


__all__ = [
    "DATA_DIR",
    "DATA_FILES",
    "Conventions",
    "Decision",
    "Registry",
    "Requirement",
    "Source",
    "SourceRef",
    "WorkPackage",
    "load_registry",
    "parse_registry",
    "read_registry_data",
]
