"""Typed records for the source, requirement, decision, and work-package registry.

The registry indexes the planning documents under ``rules-roadmap/``. It records identifiers,
source pages, owning work packages, decision links, conventions, and status. It never restates
rules text; read the cited source and the roadmap documents for behavior.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceKind = Literal[
    "rulebook", "owner_rulings", "owner_content", "errata", "faction_pack", "expansion"
]
SourceStatus = Literal["pinned", "recorded", "unverified", "missing"]
SourceRole = Literal["primary", "cross_check"]
RequirementKind = Literal["core_rule", "online_product"]
RequirementStatus = Literal["planned", "in_progress", "verified", "source_blocked"]
DecisionKind = Literal["engineering_default", "owner_ruling"]
DecisionStatus = Literal["selected", "resolved", "open"]
SliceStatus = Literal["planned", "in_progress", "complete", "source_blocked"]
Milestone = Literal["M0", "M1", "M2", "M3", "M4"]
DistanceBand = Literal["VS", "S", "M", "L"]
InterpretationStatus = Literal["recorded", "superseded"]
GateStatus = Literal["open", "satisfied"]
CaseStatus = Literal["planned", "verified"]

_UNAVAILABLE_SOURCE_STATUSES = ("unverified", "missing")

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
        if self.status in _UNAVAILABLE_SOURCE_STATUSES and self.sha256 is not None:
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
    adr: str | None = Field(default=None, pattern=r"^docs/adrs/\d{4}-[a-z0-9-]+\.md$")

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


class Interpretation(_Record):
    """A recorded reading of the source where its wording conflicts or needs an explicit policy.

    Interpretations are project decisions, not official errata.
    """

    id: str = Field(pattern=r"^I\d{2}$")
    title: str = Field(min_length=1)
    status: InterpretationStatus
    sources: tuple[SourceRef, ...] = Field(min_length=1)
    requirements: tuple[str, ...] = Field(min_length=1)


class ContentGate(_Record):
    """Missing content that limits what may be claimed complete or made selectable.

    ``requirements`` lists affected requirements; it is empty when the gate is cross-cutting.
    ``blocks`` lists slices that cannot be marked complete while the gate is open.
    """

    id: str = Field(pattern=r"^G\d{2}$")
    title: str = Field(min_length=1)
    status: GateStatus
    source_ids: tuple[str, ...] = Field(min_length=1)
    requirements: tuple[str, ...] = ()
    blocks: tuple[str, ...] = ()


class RegressionCase(_Record):
    """An acceptance case from validation-and-release.md that pins down a ruling or reading."""

    id: str = Field(pattern=r"^RC\d{2}$")
    area: str = Field(min_length=1)
    status: CaseStatus
    requirements: tuple[str, ...] = Field(min_length=1)
    decisions: tuple[str, ...] = ()
    interpretations: tuple[str, ...] = ()
    slices: tuple[str, ...] = Field(min_length=1)
    test_paths: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _check_evidence(self) -> RegressionCase:
        if self.status == "verified" and not self.test_paths:
            raise ValueError(f"{self.id}: a verified regression case needs test paths")
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


def _require_known(owner: str, label: str, ids: Iterable[str], known: Iterable[str]) -> None:
    unknown = sorted(set(ids) - set(known))
    if unknown:
        raise ValueError(f"{owner}: unknown {label} {unknown}")


def _check_source_refs(
    owner: str, refs: Iterable[SourceRef], sources: dict[str, Source], *, rulebook_primary: bool
) -> None:
    for ref in refs:
        source = sources.get(ref.source_id)
        if source is None:
            raise ValueError(f"{owner}: unknown source {ref.source_id}")
        if source.page_count is not None and ref.pages[-1] > source.page_count:
            raise ValueError(f"{owner}: page {ref.pages[-1]} beyond {source.id}")
        if rulebook_primary and ref.role == "primary" and source.kind != "rulebook":
            raise ValueError(f"{owner}: core rules cite a rulebook as primary")


class Registry(_Record):
    sources: tuple[Source, ...] = Field(min_length=1)
    requirements: tuple[Requirement, ...] = Field(min_length=1)
    decisions: tuple[Decision, ...]
    interpretations: tuple[Interpretation, ...]
    content_gates: tuple[ContentGate, ...]
    regression_cases: tuple[RegressionCase, ...]
    work_packages: tuple[WorkPackage, ...] = Field(min_length=1)
    conventions: Conventions

    @model_validator(mode="after")
    def _check_references(self) -> Registry:
        sources = _index(self.sources, "source", ordered=False)
        requirements = _index(self.requirements, "requirement", ordered=True)
        decisions = _index(self.decisions, "decision", ordered=True)
        interpretations = _index(self.interpretations, "interpretation", ordered=True)
        packages = _index(self.work_packages, "work package", ordered=True)
        slices = {s.id: s for package in self.work_packages for s in package.slices}
        _index(self.content_gates, "content gate", ordered=True)
        _index(self.regression_cases, "regression case", ordered=True)

        for requirement in self.requirements:
            _require_known(requirement.id, "packages", requirement.packages, packages)
            _require_known(requirement.id, "decisions", requirement.decisions, decisions)
            _check_source_refs(
                requirement.id,
                requirement.sources,
                sources,
                rulebook_primary=requirement.kind == "core_rule",
            )

        referenced = {d for requirement in self.requirements for d in requirement.decisions}
        unreferenced = sorted(set(decisions) - referenced)
        if unreferenced:
            raise ValueError(f"decisions not linked to any requirement: {unreferenced}")
        for decision in self.decisions:
            if decision.source_id is not None:
                _require_known(decision.id, "source", [decision.source_id], sources)

        for interpretation in self.interpretations:
            _require_known(
                interpretation.id, "requirements", interpretation.requirements, requirements
            )
            _check_source_refs(
                interpretation.id, interpretation.sources, sources, rulebook_primary=False
            )

        self._check_content_gates(sources, requirements, slices)
        self._check_regression_cases(requirements, decisions, interpretations, slices)

        conventions = self.conventions
        _require_known(
            "conventions",
            "decisions",
            (*conventions.measurement.decisions, *conventions.initiative.decisions),
            decisions,
        )

        self._check_dependencies(packages, slices)
        return self

    def _check_content_gates(
        self,
        sources: dict[str, Source],
        requirements: dict[str, Requirement],
        slices: dict[str, Slice],
    ) -> None:
        for gate in self.content_gates:
            _require_known(gate.id, "sources", gate.source_ids, sources)
            _require_known(gate.id, "requirements", gate.requirements, requirements)
            _require_known(gate.id, "slices", gate.blocks, slices)
            if gate.status == "open":
                completed = [s for s in gate.blocks if slices[s].status == "complete"]
                if completed:
                    raise ValueError(
                        f"{gate.id} is open but blocked slices are complete: {completed}"
                    )
            else:
                unavailable = [
                    s
                    for s in gate.source_ids
                    if sources[s].status in _UNAVAILABLE_SOURCE_STATUSES
                ]
                if unavailable:
                    raise ValueError(
                        f"{gate.id} is satisfied but sources are unavailable: {unavailable}"
                    )

    def _check_regression_cases(
        self,
        requirements: dict[str, Requirement],
        decisions: dict[str, Decision],
        interpretations: dict[str, Interpretation],
        slices: dict[str, Slice],
    ) -> None:
        for case in self.regression_cases:
            _require_known(case.id, "requirements", case.requirements, requirements)
            _require_known(case.id, "decisions", case.decisions, decisions)
            _require_known(case.id, "interpretations", case.interpretations, interpretations)
            _require_known(case.id, "slices", case.slices, slices)
            owners = {p for r in case.requirements for p in requirements[r].packages}
            unowned = [s for s in case.slices if s.split(".")[0] not in owners]
            if unowned:
                raise ValueError(f"{case.id}: slices {unowned} are outside its requirements")

        # Every resolved owner ruling and live interpretation must be pinned down by a case.
        # Open questions have no answer yet, so they cannot have one.
        covered = {
            link
            for case in self.regression_cases
            for link in (*case.decisions, *case.interpretations)
        }
        needed = [
            d.id for d in self.decisions if d.kind == "owner_ruling" and d.status == "resolved"
        ]
        needed += [i.id for i in self.interpretations if i.status == "recorded"]
        uncovered = [i for i in needed if i not in covered]
        if uncovered:
            raise ValueError(f"rulings without a regression case: {uncovered}")

    @staticmethod
    def _check_dependencies(packages: dict[str, WorkPackage], slices: dict[str, Slice]) -> None:
        for package in packages.values():
            for dependency in package.depends_on:
                if dependency not in packages and dependency not in slices:
                    raise ValueError(f"{package.id}: unknown dependency {dependency}")
                # Prerequisites always come from earlier packages, which also rules out cycles.
                if dependency.split(".")[0] >= package.id:
                    raise ValueError(f"{package.id}: dependency {dependency} is not earlier")
