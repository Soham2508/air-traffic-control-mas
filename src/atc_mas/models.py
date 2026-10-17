"""Shared, typed domain models.

Design decision: **all** shared domain models are Pydantic v2 models. This
gives validation at the input boundary (JSON loaders), deterministic JSON
serialisation for outputs, and models that can be used directly as CrewAI
``output_pydantic`` / Flow state types later.

Input models (``Aircraft``, ``FlightPlan``) are strict and reject unknown
fields so that malformed data fails loudly instead of being coerced.

The airspace graph itself is kept as a ``networkx.DiGraph`` (as in the
reference notebook) inside the plain ``Scenario`` container.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, computed_field

from atc_mas.config import DEFAULT_SEPARATION_MINIMA, SeparationMinima

NonEmptyStr = Annotated[str, Field(min_length=1)]


# --------------------------------------------------------------------------- #
# Input models (field names match the supplied JSON files exactly)
# --------------------------------------------------------------------------- #
class _StrictInputModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class Aircraft(_StrictInputModel):
    """An aircraft record from ``*_aircraft.json``."""

    id: NonEmptyStr
    speed_kt: float = Field(gt=0, allow_inf_nan=False, description="Speed in knots.")


class FlightPlan(_StrictInputModel):
    """A flight plan record from ``*_flight_plans.json``.

    Route length and graph membership are *not* checked here; they are
    scenario-level checks performed in :mod:`atc_mas.validation` so they can
    be reported with explicit issue codes.
    """

    aircraft_id: NonEmptyStr
    route: list[NonEmptyStr]
    departure_time_s: float = Field(ge=0, allow_inf_nan=False)
    cruise_altitude_ft: float = Field(gt=0, allow_inf_nan=False)


# --------------------------------------------------------------------------- #
# Algorithm models
# --------------------------------------------------------------------------- #
class TrajectoryPoint(BaseModel):
    """A 4D point (local x/y in NM, altitude in ft, time in s) at a waypoint."""

    model_config = ConfigDict(frozen=True)

    node_id: str
    time_s: float
    x_nm: float
    y_nm: float
    altitude_ft: float


class Conflict(BaseModel):
    """A predicted loss of separation between two aircraft (reference fields)."""

    model_config = ConfigDict(frozen=True)

    aircraft_1: str
    aircraft_2: str
    time_s: float
    horizontal_distance_nm: float
    vertical_distance_ft: float
    segment_1: list[str]
    segment_2: list[str]


# --------------------------------------------------------------------------- #
# Validation diagnostics
# --------------------------------------------------------------------------- #
class IssueCode(str, Enum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    INVALID_FORMAT = "INVALID_FORMAT"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    EMPTY_INPUT = "EMPTY_INPUT"
    GRAPH_NOT_DIRECTED = "GRAPH_NOT_DIRECTED"
    MISSING_ATTRIBUTE = "MISSING_ATTRIBUTE"
    INVALID_ATTRIBUTE = "INVALID_ATTRIBUTE"
    DUPLICATE_AIRCRAFT_ID = "DUPLICATE_AIRCRAFT_ID"
    DUPLICATE_FLIGHT_PLAN = "DUPLICATE_FLIGHT_PLAN"
    UNKNOWN_AIRCRAFT = "UNKNOWN_AIRCRAFT"
    ROUTE_TOO_SHORT = "ROUTE_TOO_SHORT"
    UNKNOWN_WAYPOINT = "UNKNOWN_WAYPOINT"
    MISSING_EDGE = "MISSING_EDGE"


class ValidationIssue(BaseModel):
    """An explicit, actionable input problem."""

    model_config = ConfigDict(frozen=True)

    code: IssueCode
    message: str
    source: str = Field(description="File name, or 'scenario' for cross-file checks.")
    location: str | None = Field(default=None, description="e.g. '[1].route' or 'node A'.")
    aircraft_id: str | None = None

    def __str__(self) -> str:
        where = f"{self.source}{' ' + self.location if self.location else ''}"
        return f"[{self.code.value}] {where}: {self.message}"


class ConflictDetectionResult(BaseModel):
    """Output of the deterministic conflict-detection tool.

    ``is_valid`` is ``False`` whenever any validation issue was found. In that
    case the analysis is incomplete and a zero conflict count **must not** be
    interpreted as "no conflicts".
    """

    conflicts: list[Conflict] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    separation_minima: SeparationMinima = DEFAULT_SEPARATION_MINIMA
    analysed_aircraft_ids: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_valid(self) -> bool:
        return not self.validation_issues

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


# --------------------------------------------------------------------------- #
# Resolution models (tactical resolution is NOT implemented in this scaffold)
# --------------------------------------------------------------------------- #
class ResolutionStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"  # placeholder planner produced nothing
    UNRESOLVED = "UNRESOLVED"  # no acceptable maneuver found
    PROPOSED = "PROPOSED"  # maneuver exists but has not been re-checked
    REJECTED = "REJECTED"  # re-check failed
    VALIDATED = "VALIDATED"  # full scenario re-check found zero conflicts/issues


class ResolutionProposal(BaseModel):
    """A (possibly empty) tactical resolution for one conflict."""

    conflict: Conflict
    status: ResolutionStatus
    summary: str
    modified_flight_plans: list[FlightPlan] = Field(default_factory=list)
    validation_notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Scenario / run-level models
# --------------------------------------------------------------------------- #
class InputFiles(BaseModel):
    airspace: str
    aircraft: str
    flight_plans: str


class Waypoint(BaseModel):
    id: str
    latitude: float
    longitude: float


class AirspaceEdge(BaseModel):
    source: str
    target: str
    distance_nm: float


class ScenarioSummary(BaseModel):
    """Serialisable view of a validated scenario."""

    waypoints: list[Waypoint]
    edges: list[AirspaceEdge]
    aircraft: list[Aircraft]
    flight_plans: list[FlightPlan]


@dataclass
class Scenario:
    """A loaded and validated scenario, including the NetworkX graph."""

    graph: nx.DiGraph
    aircraft: list[Aircraft]
    flight_plans: list[FlightPlan]
    input_files: InputFiles

    def summary(self) -> ScenarioSummary:
        return ScenarioSummary(
            waypoints=[
                Waypoint(id=str(n), latitude=float(d["latitude"]), longitude=float(d["longitude"]))
                for n, d in self.graph.nodes(data=True)
            ],
            edges=[
                AirspaceEdge(source=str(u), target=str(v), distance_nm=float(d["distance_nm"]))
                for u, v, d in self.graph.edges(data=True)
            ],
            aircraft=list(self.aircraft),
            flight_plans=list(self.flight_plans),
        )


class AnalysisStatus(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    NO_CONFLICTS_DETECTED = "NO_CONFLICTS_DETECTED"
    CONFLICTS_UNRESOLVED = "CONFLICTS_UNRESOLVED"
    CONFLICTS_RESOLVED_VALIDATED = "CONFLICTS_RESOLVED_VALIDATED"


def determine_analysis_status(
    detection: ConflictDetectionResult, resolutions: list[ResolutionProposal]
) -> AnalysisStatus:
    """Derive the overall status from structured data only.

    ``CONFLICTS_RESOLVED_VALIDATED`` requires at least one ``VALIDATED``
    proposal. ``VALIDATED`` is only assigned by
    :func:`atc_mas.tools.maneuver_planning.validate_resolution`, which re-runs
    detection on the *whole* modified scenario.
    """
    if not detection.is_valid:
        return AnalysisStatus.INVALID_INPUT
    if not detection.has_conflicts:
        return AnalysisStatus.NO_CONFLICTS_DETECTED
    if any(r.status is ResolutionStatus.VALIDATED for r in resolutions):
        return AnalysisStatus.CONFLICTS_RESOLVED_VALIDATED
    return AnalysisStatus.CONFLICTS_UNRESOLVED


class ATCAnalysis(BaseModel):
    """Complete structured result of one batch analysis (JSON output root)."""

    simulation_only: Literal[True] = True
    input_files: InputFiles
    scenario: ScenarioSummary | None = None
    detection: ConflictDetectionResult
    resolutions: list[ResolutionProposal] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def analysis_status(self) -> AnalysisStatus:
        return determine_analysis_status(self.detection, self.resolutions)
