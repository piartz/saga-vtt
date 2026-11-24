"""Typed records for the source, requirement, decision, and work-package registry.

The registry indexes the planning documents under ``rules-roadmap/``. It records identifiers,
source pages, owning work packages, decision links, conventions, and status. It never restates
rules text; read the cited source and the roadmap documents for behavior.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceKind = Literal["rulebook", "owner_rulings", "errata", "faction_pack", "expansion"]
SourceStatus = Literal["pinned", "recorded", "unverified", "missing"]
SourceRole = Literal["primary", "cross_check"]
RequirementKind = Literal["core_rule", "online_product"]
RequirementStatus = Literal["planned", "in_progress", "verified", "source_blocked"]
DecisionKind = Literal["engineering_default", "owner_ruling"]
DecisionStatus = Literal["selected", "resolved", "open"]
SliceStatus = Literal["planned", "in_progress", "complete", "source_blocked"]
Milestone = Literal["M0", "M1", "M2", "M3", "M4"]
DistanceBand = Literal["VS", "S", "M", "L"]

# One inch is exactly 25.4 mm; keep the arithmetic in integers.
_TENTHS_OF_MM_PER_INCH = 254


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Source(_Record):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]*$")
    kind: SourceKind
    title: str = Field(min_length=1)
    status: SourceStatus
    edition: str | None = None
    isbn: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    page_count: int | None = Field(default=None, gt=0)
    local_filename: str | None = None

    @model_validator(mode="after")
    def _check_status(self) -> Source:
        if self.status == "pinned" and (self.sha256 is None or self.page_count is None):
            raise ValueError(f"pinned source {self.id} needs sha256 and page_count")
        if self.status in ("unverified", "missing") and self.sha256 is not None:
            raise ValueError(f"source {self.id} is {self.status} and cannot carry a fingerprint")
        return self


class SourceRef(_Record):
    source_id: str
    pages: tuple[int, ...] = Field(min_length=1)
    role: SourceRole = "primary"

    @model_validator(mode="after")
    def _check_pages(self) -> SourceRef:
        if self.pages[0] < 1 or list(self.pages) != sorted(set(self.pages)):
            raise ValueError(f"pages for {self.source_id} must be positive, unique, and sorted")
        return self


class Requirement(_Record):
    id: str = Field(pattern=r"^R\d{2}$")
    title: str = Field(min_length=1)
    kind: RequirementKind
    status: RequirementStatus
    packages: tuple[str, ...] = Field(min_length=1)
    sources: tuple[SourceRef, ...] = ()
    decisions: tuple[str, ...] = ()
    implementation_paths: tuple[str, ...] = ()
    test_paths: tuple[str, ...] = ()
    content_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _check_provenance(self) -> Requirement:
        if self.kind == "core_rule" and not any(ref.role == "primary" for ref in self.sources):
            raise ValueError(f"{self.id}: a core rule needs a primary source reference")
        if self.kind == "online_product" and not any(d.startswith("D") for d in self.decisions):
            raise ValueError(f"{self.id}: a product requirement needs an engineering decision")
        if self.status == "verified" and not (self.implementation_paths and self.test_paths):
            raise ValueError(f"{self.id}: a verified requirement needs implementation and tests")
        return self


class Decision(_Record):
    id: str = Field(pattern=r"^[DQ]\d{2}$")
    kind: DecisionKind
    title: str = Field(min_length=1)
    status: DecisionStatus
    source_id: str | None = None
    adr: str | None = None

    @model_validator(mode="after")
    def _check_kind(self) -> Decision:
        if self.id.startswith("D"):
            if self.kind != "engineering_default" or self.status != "selected":
                raise ValueError(f"{self.id}: D-decisions are selected engineering defaults")
            if self.source_id is not None:
                raise ValueError(f"{self.id}: engineering defaults have no external source")
        else:
            if self.kind != "owner_ruling" or self.status == "selected":
                raise ValueError(f"{self.id}: Q-decisions are owner rulings, resolved or open")
            if self.status == "resolved" and self.source_id is None:
                raise ValueError(f"{self.id}: a resolved ruling needs its source")
        return self


class Slice(_Record):
    id: str = Field(pattern=r"^P\d{2}\.\d+$")
    title: str = Field(min_length=1)
    status: SliceStatus


class WorkPackage(_Record):
    id: str = Field(pattern=r"^P\d{2}$")
    title: str = Field(min_length=1)
    milestone: Milestone
    depends_on: tuple[str, ...] = ()
    slices: tuple[Slice, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_slices(self) -> WorkPackage:
        expected = [f"{self.id}.{n}" for n in range(1, len(self.slices) + 1)]
        if [s.id for s in self.slices] != expected:
            raise ValueError(f"{self.id}: slices must be numbered {', '.join(expected)}")
        return self

    @property
    def is_complete(self) -> bool:
        return all(s.status == "complete" for s in self.slices)


class DistanceBandsInches(_Record):
    VS: int = Field(gt=0)
    S: int = Field(gt=0)
    M: int = Field(gt=0)
    L: int = Field(gt=0)


class MeasurementConventions(_Record):
    """Selected measurement conventions (Q01/Q03/D03); not yet implemented in geometry."""

    player_facing_unit: Literal["inch"]
    distance_bands_inches: DistanceBandsInches
    distance_label_aliases: dict[str, DistanceBand]
    table_width_inches: int = Field(gt=0)
    table_depth_inches: int = Field(gt=0)
    ruler_width_inches: int = Field(gt=0)
    internal_units_per_mm: int = Field(gt=0)
    decisions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_exact_conversion(self) -> MeasurementConventions:
        bands = self.distance_bands_inches
        lengths = {
            **{f"band {name}": inches for name, inches in bands.model_dump().items()},
            "table width": self.table_width_inches,
            "table depth": self.table_depth_inches,
            "ruler width": self.ruler_width_inches,
        }
        for label, inches in lengths.items():
            if (inches * _TENTHS_OF_MM_PER_INCH * self.internal_units_per_mm) % 10:
                raise ValueError(f"{label} is not an exact number of internal units")
        return self


class InitiativeConventions(_Record):
    clash_tie_break: Literal["coin_toss"]
    decisions: tuple[str, ...] = Field(min_length=1)


class Conventions(_Record):
    measurement: MeasurementConventions
    initiative: InitiativeConventions


class _HasId(Protocol):
    @property
    def id(self) -> str: ...


_T = TypeVar("_T", bound=_HasId)


def _index(records: Iterable[_T], label: str, *, ordered: bool) -> dict[str, _T]:
    index: dict[str, _T] = {}
    for record in records:
        if record.id in index:
            raise ValueError(f"duplicate {label} id {record.id}")
        index[record.id] = record
    if ordered and list(index) != sorted(index):
        raise ValueError(f"{label} records must be sorted by id")
    return index


class Registry(_Record):
    sources: tuple[Source, ...] = Field(min_length=1)
    requirements: tuple[Requirement, ...] = Field(min_length=1)
    decisions: tuple[Decision, ...]
    work_packages: tuple[WorkPackage, ...] = Field(min_length=1)
    conventions: Conventions

    @model_validator(mode="after")
    def _check_references(self) -> Registry:
        sources = _index(self.sources, "source", ordered=False)
        _index(self.requirements, "requirement", ordered=True)
        decisions = _index(self.decisions, "decision", ordered=True)
        packages = _index(self.work_packages, "work package", ordered=True)

        for requirement in self.requirements:
            self._check_requirement(requirement, sources, decisions, packages)

        referenced = {d for requirement in self.requirements for d in requirement.decisions}
        unreferenced = sorted(set(decisions) - referenced)
        if unreferenced:
            raise ValueError(f"decisions not linked to any requirement: {unreferenced}")
        for decision in self.decisions:
            if decision.source_id is not None and decision.source_id not in sources:
                raise ValueError(f"{decision.id}: unknown source {decision.source_id}")

        convention_refs = (
            *self.conventions.measurement.decisions,
            *self.conventions.initiative.decisions,
        )
        unknown_refs = sorted(set(convention_refs) - set(decisions))
        if unknown_refs:
            raise ValueError(f"conventions cite unknown decisions: {unknown_refs}")

        self._check_dependencies(packages)
        return self

    @staticmethod
    def _check_requirement(
        requirement: Requirement,
        sources: dict[str, Source],
        decisions: dict[str, Decision],
        packages: dict[str, WorkPackage],
    ) -> None:
        unknown_packages = sorted(set(requirement.packages) - set(packages))
        if unknown_packages:
            raise ValueError(f"{requirement.id}: unknown packages {unknown_packages}")
        unknown_decisions = sorted(set(requirement.decisions) - set(decisions))
        if unknown_decisions:
            raise ValueError(f"{requirement.id}: unknown decisions {unknown_decisions}")
        for ref in requirement.sources:
            source = sources.get(ref.source_id)
            if source is None:
                raise ValueError(f"{requirement.id}: unknown source {ref.source_id}")
            if source.page_count is not None and ref.pages[-1] > source.page_count:
                raise ValueError(f"{requirement.id}: page {ref.pages[-1]} beyond {source.id}")
            if (
                requirement.kind == "core_rule"
                and ref.role == "primary"
                and source.kind != "rulebook"
            ):
                raise ValueError(f"{requirement.id}: core rules cite a rulebook as primary")

    @staticmethod
    def _check_dependencies(packages: dict[str, WorkPackage]) -> None:
        slice_ids = {s.id for package in packages.values() for s in package.slices}
        for package in packages.values():
            for dependency in package.depends_on:
                if dependency not in packages and dependency not in slice_ids:
                    raise ValueError(f"{package.id}: unknown dependency {dependency}")
                # Prerequisites always come from earlier packages, which also rules out cycles.
                if dependency.split(".")[0] >= package.id:
                    raise ValueError(f"{package.id}: dependency {dependency} is not earlier")
