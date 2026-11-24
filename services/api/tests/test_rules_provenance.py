"""Registry integrity and agreement with the rules-roadmap planning documents."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.rules.provenance import Registry, load_registry, parse_registry, read_registry_data

REPO_ROOT = Path(__file__).resolve().parents[3]
ROADMAP = REPO_ROOT / "rules-roadmap"
LAST_PACKAGE = 15


def _roadmap(name: str) -> str:
    return (ROADMAP / name).read_text(encoding="utf-8")


def _expand_ids(text: str, prefix: str, last: int) -> list[str]:
    """Expand e.g. 'P02, P09-P11, P13' or 'P05 onward' into explicit sorted IDs."""
    ids: set[str] = set()
    pattern = rf"{prefix}(\d{{2}})(?:-{prefix}(\d{{2}})|( onward))?"
    for match in re.finditer(pattern, text):
        start = int(match.group(1))
        end = last if match.group(3) else int(match.group(2) or start)
        ids.update(f"{prefix}{n:02d}" for n in range(start, end + 1))
    return sorted(ids)


def _expand_pages(text: str) -> list[int]:
    pages: set[int] = set()
    for match in re.finditer(r"(\d+)(?:-(\d+))?", text):
        start = int(match.group(1))
        pages.update(range(start, int(match.group(2) or start) + 1))
    return sorted(pages)


def _cited_decisions(text: str) -> set[str]:
    return set(re.findall(r"\b[DQ]\d{2}\b", text))


@dataclass
class CoverageEntry:
    title: str | None
    packages: list[str]
    decisions: set[str]
    interpretations: set[str] = field(default_factory=set)
    pages: list[int] = field(default_factory=list)
    cross_check_pages: list[int] = field(default_factory=list)


def _coverage() -> tuple[dict[str, CoverageEntry], dict[str, CoverageEntry]]:
    core_text, online_text = _roadmap("rules-coverage.md").split(
        "\n## Online product requirements", 1
    )
    core: dict[str, CoverageEntry] = {}
    parts = re.split(r"^### (R\d{2}) - (.+)$", core_text, flags=re.M)
    for requirement_id, title, body in zip(parts[1::3], parts[2::3], parts[3::3]):
        line = re.search(r"^\*\*Source:\*\* (.+?)\. \*\*Packages?:\*\* (.+?)\.$", body, re.M)
        assert line is not None, f"{requirement_id} has no Source/Packages line"
        primary, _, cross_check = line.group(1).partition("cross-check")
        core[requirement_id] = CoverageEntry(
            title=title.strip(),
            packages=_expand_ids(line.group(2), "P", LAST_PACKAGE),
            decisions=_cited_decisions(body),
            interpretations=set(re.findall(r"\bI\d{2}\b", body)),
            pages=_expand_pages(primary),
            cross_check_pages=_expand_pages(cross_check),
        )
    online: dict[str, CoverageEntry] = {}
    for row in re.finditer(r"^\| (R\d{2}) \| (.+?) \| (.+?) \| (.+?) \|$", online_text, re.M):
        online[row.group(1)] = CoverageEntry(
            title=None,
            packages=_expand_ids(row.group(3), "P", LAST_PACKAGE),
            decisions=_cited_decisions(row.group(0)),
        )
    return core, online


def _pages(registry: Registry, requirement_id: str, role: str) -> list[int]:
    requirement = next(r for r in registry.requirements if r.id == requirement_id)
    return sorted({p for ref in requirement.sources if ref.role == role for p in ref.pages})


def test_registry_ids_are_complete_and_contiguous() -> None:
    registry = load_registry()

    assert [r.id for r in registry.requirements] == [f"R{n:02d}" for n in range(1, 35)]
    assert [p.id for p in registry.work_packages] == [
        f"P{n:02d}" for n in range(0, LAST_PACKAGE + 1)
    ]
    assert [d.id for d in registry.decisions] == [f"D{n:02d}" for n in range(1, 16)] + [
        f"Q{n:02d}" for n in range(1, 12)
    ]


def test_every_requirement_has_a_source_and_owner_package() -> None:
    for requirement in load_registry().requirements:
        assert requirement.packages, requirement.id
        assert requirement.sources or requirement.decisions, requirement.id


def test_requirements_match_rules_coverage() -> None:
    registry = load_registry()
    by_id = {r.id: r for r in registry.requirements}
    core, online = _coverage()

    assert sorted(core) + sorted(online) == list(by_id)
    for requirement_id, entry in core.items():
        requirement = by_id[requirement_id]
        assert requirement.kind == "core_rule"
        assert requirement.title == entry.title
        assert list(requirement.packages) == entry.packages
        assert _pages(registry, requirement_id, "primary") == entry.pages
        assert _pages(registry, requirement_id, "cross_check") == entry.cross_check_pages
        assert entry.decisions <= set(requirement.decisions), requirement_id
    for requirement_id, entry in online.items():
        requirement = by_id[requirement_id]
        assert requirement.kind == "online_product"
        assert list(requirement.packages) == entry.packages
        assert entry.decisions <= set(requirement.decisions), requirement_id


def test_work_packages_match_implementation_plan() -> None:
    plan = _roadmap("implementation-plan.md")
    registry = load_registry()

    headings = dict(re.findall(r"^## (P\d{2}) - (.+)$", plan, re.M))
    assert {p.id: p.title for p in registry.work_packages} == headings

    slices = re.findall(r"^\d+\. `(P\d{2}\.\d+)`:", plan, re.M)
    assert [s.id for p in registry.work_packages for s in p.slices] == slices

    milestone_rows = re.findall(r"^\| (M\d): [^|]+\| P(\d{2})-P(\d{2}) \|", plan, re.M)
    milestones = {
        f"P{n:02d}": milestone
        for milestone, first, last in milestone_rows
        for n in range(int(first), int(last) + 1)
    }
    assert {p.id: p.milestone for p in registry.work_packages} == milestones


def _closure(direct: dict[str, set[str]]) -> dict[str, set[str]]:
    closed: dict[str, set[str]] = {}

    def visit(node: str) -> set[str]:
        if node not in closed:
            closed[node] = set()
            for dependency in direct.get(node, set()):
                closed[node] |= {dependency} | visit(dependency)
        return closed[node]

    for node in direct:
        visit(node)
    return closed


def test_dependencies_match_plan_graph() -> None:
    plan = _roadmap("implementation-plan.md")
    graph = re.search(r"```mermaid\n(.*?)```", plan, re.S)
    assert graph is not None
    planned: dict[str, set[str]] = {}
    for line in graph.group(1).splitlines():
        nodes = re.split(r"\s*-->(?:\|[^|]*\|)?\s*", line.strip())
        for prerequisite, package_id in zip(nodes, nodes[1:]):
            planned.setdefault(package_id, set()).add(prerequisite)

    registered = {
        p.id: {d.split(".")[0] for d in p.depends_on} for p in load_registry().work_packages
    }
    def nonempty(graph: dict[str, set[str]]) -> dict[str, set[str]]:
        return {node: deps for node, deps in _closure(graph).items() if deps}

    assert nonempty(registered) == nonempty(planned)


def test_decisions_match_decision_register() -> None:
    register = _roadmap("decisions-and-source-gaps.md")
    rows = dict(re.findall(r"^\| ([DQ]\d{2}) \| (.+)$", register, re.M))
    decisions = load_registry().decisions

    assert [d.id for d in decisions] == list(rows)
    for decision in decisions:
        if decision.kind == "owner_ruling":
            assert ("**Resolved" in rows[decision.id]) == (decision.status == "resolved")


def test_core_source_fingerprint_matches_coverage_doc() -> None:
    core = next(s for s in load_registry().sources if s.id == "CORE-2022")
    coverage = _roadmap("rules-coverage.md")

    assert core.status == "pinned"
    assert f"SHA-256 `{core.sha256}`" in coverage
    assert core.isbn is not None and core.isbn in coverage


def test_local_rulebook_matches_pinned_fingerprint() -> None:
    core = next(s for s in load_registry().sources if s.id == "CORE-2022")
    assert core.local_filename is not None
    path = REPO_ROOT / "rules" / core.local_filename
    if not path.exists():
        pytest.skip("local rulebook reference is not present (it is never committed)")

    assert hashlib.sha256(path.read_bytes()).hexdigest() == core.sha256


def test_unverified_and_missing_sources_stay_unpinned() -> None:
    statuses = {s.id: s.status for s in load_registry().sources}

    assert statuses["ERRATA"] == "unverified"
    assert statuses["FACTION-A"] == statuses["FACTION-B"] == "missing"


def test_measurement_conventions_match_owner_rulings_in_coverage() -> None:
    measurement = load_registry().conventions.measurement
    coverage = _roadmap("rules-coverage.md")
    bands = re.search(r"VS/S/M/L = (\d+)/(\d+)/(\d+)/(\d+) inches", coverage)
    table = re.search(r"(\d+) x (\d+) inch table", coverage)
    assert bands is not None and table is not None

    assert measurement.distance_bands_inches.model_dump() == dict(
        zip(["VS", "S", "M", "L"], map(int, bands.groups()))
    )
    assert (measurement.table_width_inches, measurement.table_depth_inches) == tuple(
        map(int, table.groups())
    )
    assert measurement.distance_label_aliases == {"C": "S"}
    assert measurement.ruler_width_inches == 1
    assert load_registry().conventions.initiative.clash_tie_break == "coin_toss"


def _table_first_column(text: str, heading: str) -> list[str]:
    section = text.split(f"\n{heading}\n", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| (.+?) \|", section, re.M)
    return [row for row in rows[1:] if not set(row) <= set("-: ")]


def test_interpretations_are_cited_where_they_apply() -> None:
    interpretations = load_registry().interpretations
    core, _ = _coverage()

    for requirement_id, entry in core.items():
        linked = {i.id for i in interpretations if requirement_id in i.requirements}
        assert entry.interpretations == linked, requirement_id


def test_content_gates_match_missing_content_table() -> None:
    register = _roadmap("decisions-and-source-gaps.md")
    rows = _table_first_column(register, "## Missing content and scope boundaries")

    assert [g.title for g in load_registry().content_gates] == rows


def test_generic_board_gate_blocks_generic_pack_completion() -> None:
    registry = load_registry()
    gate = next(g for g in registry.content_gates if g.id == "G01")
    board = next(s for s in registry.sources if s.id in gate.source_ids)

    assert gate.status == "open"
    assert board.status == "missing"
    assert set(gate.blocks) == {"P12.1", "P12.2", "P12.3"}


def test_regression_cases_match_validation_table() -> None:
    validation = _roadmap("validation-and-release.md")
    areas = _table_first_column(validation, "## High-value regression examples")
    cases = load_registry().regression_cases

    assert len(areas) == len(set(areas))
    assert [c.area for c in cases] == [a for a in areas if a in {c.area for c in cases}]


def test_every_resolved_ruling_has_a_regression_case() -> None:
    registry = load_registry()
    covered = {
        link
        for case in registry.regression_cases
        for link in (*case.decisions, *case.interpretations)
    }

    for decision in registry.decisions:
        if decision.kind == "owner_ruling" and decision.status == "resolved":
            assert decision.id in covered, decision.id
    for interpretation in registry.interpretations:
        assert interpretation.id in covered, interpretation.id


def test_verified_records_point_at_existing_paths() -> None:
    registry = load_registry()
    evidence = [
        (r.id, (*r.implementation_paths, *r.test_paths))
        for r in registry.requirements
        if r.status == "verified"
    ]
    evidence += [(c.id, c.test_paths) for c in registry.regression_cases if c.status == "verified"]

    for record_id, paths in evidence:
        for path in paths:
            assert (REPO_ROOT / path).exists(), f"{record_id}: {path} is missing"


ADR_DIR = REPO_ROOT / "docs" / "adrs"
ADR_SECTIONS = ["## Status", "## Context", "## Decision", "## Consequences"]


def _adr_files() -> list[Path]:
    return sorted(p for p in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md") if p.name[:4] != "0000")


def test_adrs_follow_the_template() -> None:
    adrs = _adr_files()
    assert adrs, "expected recorded ADRs"

    for number, path in enumerate(adrs, 1):
        text = path.read_text(encoding="utf-8")
        assert path.name.startswith(f"{number:04d}-"), f"ADR numbering gap at {path.name}"
        assert text.startswith(f"# ADR {number:04d}: "), path.name
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        assert headings == ADR_SECTIONS, path.name


def test_adrs_and_decision_links_agree() -> None:
    decisions = load_registry().decisions
    linked: dict[str, set[str]] = {}
    for decision in decisions:
        if decision.adr is not None:
            assert (REPO_ROOT / decision.adr).exists(), f"{decision.id}: {decision.adr} missing"
            linked.setdefault(decision.adr, set()).add(decision.id)

    for path in _adr_files():
        status = path.read_text(encoding="utf-8").split("## Context", 1)[0]
        recorded = re.search(r"Records decisions? (.+?)(?: and owner rulings .+?)?\.", status)
        assert recorded is not None, f"{path.name} names no decisions in its Status"
        relative = str(path.relative_to(REPO_ROOT))
        assert set(re.findall(r"\bD\d{2}\b", recorded.group(1))) == linked.get(relative), path.name


def test_open_question_can_gate_requirements() -> None:
    data: dict[str, Any] = read_registry_data()
    data["decisions"].append(
        {"id": "Q12", "kind": "owner_ruling", "title": "Unsettled question", "status": "open"}
    )
    _requirement(data, "R01")["decisions"].append("Q12")

    registry = parse_registry(data)

    assert next(d for d in registry.decisions if d.id == "Q12").status == "open"


def _requirement(data: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    return next(r for r in data["requirements"] if r["id"] == requirement_id)


def _package(data: dict[str, Any], package_id: str) -> dict[str, Any]:
    return next(p for p in data["work_packages"] if p["id"] == package_id)


def _record(data: dict[str, Any], collection: str, record_id: str) -> dict[str, Any]:
    return next(r for r in data[collection] if r["id"] == record_id)


def _complete_blocked_slice(data: dict[str, Any]) -> None:
    _package(data, "P12")["slices"][0]["status"] = "complete"


def _drop_case(data: dict[str, Any], case_id: str) -> None:
    data["regression_cases"].remove(_record(data, "regression_cases", case_id))


def _unreferenced_decision(data: dict[str, Any]) -> None:
    data["decisions"].append(
        {"id": "Q12", "kind": "owner_ruling", "title": "Unlinked", "status": "open"}
    )


INVALID_MUTATIONS: dict[str, Callable[[dict[str, Any]], None]] = {
    "duplicate requirement": lambda d: d["requirements"].append(_requirement(d, "R01")),
    "unknown package": lambda d: _requirement(d, "R01")["packages"].append("P16"),
    "unknown decision": lambda d: _requirement(d, "R01")["decisions"].append("Q99"),
    "unreferenced decision": _unreferenced_decision,
    "page beyond source": lambda d: _requirement(d, "R25")["sources"][0]["pages"].append(53),
    "unsorted pages": lambda d: _requirement(d, "R01")["sources"][0]["pages"].reverse(),
    "core rule without source": lambda d: _requirement(d, "R09").update(sources=[]),
    "verified without evidence": lambda d: _requirement(d, "R09").update(status="verified"),
    "pinned source without hash": lambda d: d["sources"][0].pop("sha256"),
    "missing source with hash": lambda d: _record(d, "sources", "FACTION-A").update(
        sha256="0" * 64
    ),
    "forward dependency": lambda d: _package(d, "P01")["depends_on"].append("P02"),
    "unknown dependency": lambda d: _package(d, "P02")["depends_on"].append("P01.9"),
    "misnumbered slice": lambda d: _package(d, "P00")["slices"][1].update(id="P00.5"),
    "unknown field": lambda d: _requirement(d, "R01").update(summary="rules text"),
    "inexact conversion": lambda d: d["conventions"]["measurement"].update(internal_units_per_mm=3),
    "ruling as default": lambda d: d["decisions"][15].update(kind="engineering_default"),
    "unknown convention decision": lambda d: d["conventions"]["initiative"]["decisions"].append(
        "D99"
    ),
    "interpretation page beyond source": lambda d: _record(d, "interpretations", "I01")[
        "sources"
    ][0]["pages"].append(60),
    "interpretation of unknown requirement": lambda d: _record(d, "interpretations", "I02")[
        "requirements"
    ].append("R99"),
    "open gate with complete slice": _complete_blocked_slice,
    "satisfied gate with missing source": lambda d: _record(d, "content_gates", "G01").update(
        status="satisfied"
    ),
    "gate blocking unknown slice": lambda d: _record(d, "content_gates", "G02")["blocks"].append(
        "P16.1"
    ),
    "case slice outside requirements": lambda d: _record(d, "regression_cases", "RC07")[
        "slices"
    ].append("P02.1"),
    "case with unknown interpretation": lambda d: _record(d, "regression_cases", "RC02")[
        "interpretations"
    ].append("I09"),
    "verified case without tests": lambda d: _record(d, "regression_cases", "RC09").update(
        status="verified"
    ),
    "adr outside docs/adrs": lambda d: _record(d, "decisions", "D01").update(adr="notes/seats.md"),
    "ruling without a case": lambda d: _drop_case(d, "RC12"),
    "interpretation without a case": lambda d: _drop_case(d, "RC02"),
}


@pytest.mark.parametrize("mutation", INVALID_MUTATIONS.values(), ids=INVALID_MUTATIONS.keys())
def test_invalid_registry_data_is_rejected(
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    data: dict[str, Any] = read_registry_data()
    mutation(data)

    with pytest.raises(ValidationError):
        parse_registry(data)
