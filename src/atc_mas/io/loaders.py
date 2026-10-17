"""Loaders for the airspace GraphML and aircraft / flight-plan JSON files.

Every loader either returns fully validated data or raises
:class:`InputValidationError` carrying **all** issues it found. Invalid
records are never silently dropped.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

import networkx as nx
from pydantic import BaseModel, ValidationError

from atc_mas.models import Aircraft, FlightPlan, InputFiles, IssueCode, Scenario, ValidationIssue
from atc_mas.validation import validate_aircraft_ids, validate_airspace_graph, validate_scenario

PathLike = str | Path
ModelT = TypeVar("ModelT", bound=BaseModel)


class InputValidationError(Exception):
    """Raised when input files are missing, malformed or inconsistent."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = list(issues)
        lines = "\n".join(f"  - {issue}" for issue in self.issues)
        super().__init__(f"{len(self.issues)} input validation issue(s):\n{lines}")


def _issue(code: IssueCode, message: str, source: str, location: str | None = None) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, source=source, location=location)


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise InputValidationError([_issue(IssueCode.FILE_NOT_FOUND, f"file not found: {path}", path.name)])


# --------------------------------------------------------------------------- #
# GraphML
# --------------------------------------------------------------------------- #
def load_airspace_graph(path: PathLike) -> nx.DiGraph:
    """Load and validate a directed airspace graph from GraphML."""
    path = Path(path)
    _require_file(path)
    try:
        graph = nx.read_graphml(path)
    except Exception as exc:  # noqa: BLE001 - parser raises many unrelated types
        raise InputValidationError(
            [_issue(IssueCode.INVALID_FORMAT, f"could not parse GraphML: {exc}", path.name)]
        ) from exc

    issues = validate_airspace_graph(graph, source=path.name)
    if issues:
        raise InputValidationError(issues)
    return graph


# --------------------------------------------------------------------------- #
# JSON
# --------------------------------------------------------------------------- #
def _load_json_records(path: Path, model: type[ModelT]) -> list[ModelT]:
    _require_file(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputValidationError(
            [_issue(IssueCode.INVALID_FORMAT, f"invalid JSON: {exc.msg}", path.name, f"line {exc.lineno} col {exc.colno}")]
        ) from exc
    except UnicodeDecodeError as exc:
        raise InputValidationError([_issue(IssueCode.INVALID_FORMAT, f"not UTF-8 text: {exc}", path.name)]) from exc

    if not isinstance(raw, list):
        raise InputValidationError(
            [_issue(IssueCode.SCHEMA_ERROR, f"top-level JSON value must be a list, got {type(raw).__name__}", path.name)]
        )
    if not raw:
        raise InputValidationError([_issue(IssueCode.EMPTY_INPUT, "list contains no records", path.name)])

    records: list[ModelT] = []
    issues: list[ValidationIssue] = []
    for index, item in enumerate(raw):
        try:
            records.append(model.model_validate(item))
        except ValidationError as exc:
            for err in exc.errors():
                field = ".".join(str(part) for part in err["loc"])
                location = f"[{index}].{field}" if field else f"[{index}]"
                issues.append(_issue(IssueCode.SCHEMA_ERROR, err["msg"], path.name, location))
    if issues:
        raise InputValidationError(issues)
    return records


def load_aircraft(path: PathLike) -> list[Aircraft]:
    """Load aircraft records (``id``, ``speed_kt``) and reject duplicate IDs."""
    path = Path(path)
    aircraft = _load_json_records(path, Aircraft)
    issues = validate_aircraft_ids(aircraft, source=path.name)
    if issues:
        raise InputValidationError(issues)
    return aircraft


def load_flight_plans(path: PathLike) -> list[FlightPlan]:
    """Load flight-plan records. Graph/aircraft cross-checks happen in :func:`load_scenario`."""
    return _load_json_records(Path(path), FlightPlan)


# --------------------------------------------------------------------------- #
# Scenario
# --------------------------------------------------------------------------- #
def load_scenario(airspace_path: PathLike, aircraft_path: PathLike, flight_plans_path: PathLike) -> Scenario:
    """Load all three inputs and run cross-file validation.

    File-level problems from all three files are collected before raising so
    the user sees every problem at once.
    """
    issues: list[ValidationIssue] = []
    graph = aircraft = plans = None

    try:
        graph = load_airspace_graph(airspace_path)
    except InputValidationError as exc:
        issues.extend(exc.issues)
    try:
        aircraft = load_aircraft(aircraft_path)
    except InputValidationError as exc:
        issues.extend(exc.issues)
    try:
        plans = load_flight_plans(flight_plans_path)
    except InputValidationError as exc:
        issues.extend(exc.issues)

    if issues or graph is None or aircraft is None or plans is None:
        raise InputValidationError(issues)

    cross_issues = validate_scenario(aircraft, plans, graph, source=Path(flight_plans_path).name)
    if cross_issues:
        raise InputValidationError(cross_issues)

    return Scenario(
        graph=graph,
        aircraft=aircraft,
        flight_plans=plans,
        input_files=InputFiles(
            airspace=str(airspace_path), aircraft=str(aircraft_path), flight_plans=str(flight_plans_path)
        ),
    )
