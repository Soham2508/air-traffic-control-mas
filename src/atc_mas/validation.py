"""Scenario-level validation shared by the loaders and the detection tool.

Kept separate from :mod:`atc_mas.io.loaders` so that the deterministic
conflict-detection tool can re-check its inputs when called directly (e.g. by
tests or by a CrewAI tool) without depending on file I/O.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable

import networkx as nx

from atc_mas.models import Aircraft, FlightPlan, IssueCode, ValidationIssue

SCENARIO_SOURCE = "scenario"


def _as_finite_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def validate_airspace_graph(graph: nx.Graph, source: str = "airspace") -> list[ValidationIssue]:
    """Check the graph is a non-empty simple digraph with the required attributes."""
    issues: list[ValidationIssue] = []

    def add(code: IssueCode, message: str, location: str | None = None) -> None:
        issues.append(ValidationIssue(code=code, message=message, source=source, location=location))

    if not graph.is_directed():
        add(IssueCode.GRAPH_NOT_DIRECTED, "airspace graph must be directed (edgedefault='directed')")
    if graph.is_multigraph():
        add(IssueCode.INVALID_FORMAT, "parallel edges (multigraph) are not supported")
    if graph.number_of_nodes() == 0:
        add(IssueCode.EMPTY_INPUT, "airspace graph contains no nodes")

    for node_id, data in graph.nodes(data=True):
        loc = f"node {node_id}"
        for attr, lo, hi in (("latitude", -90.0, 90.0), ("longitude", -180.0, 180.0)):
            if attr not in data:
                add(IssueCode.MISSING_ATTRIBUTE, f"missing '{attr}' attribute", loc)
                continue
            value = _as_finite_float(data[attr])
            if value is None or not lo <= value <= hi:
                add(IssueCode.INVALID_ATTRIBUTE, f"'{attr}'={data[attr]!r} must be a number in [{lo}, {hi}]", loc)

    for u, v, data in graph.edges(data=True):
        loc = f"edge {u}->{v}"
        if "distance_nm" not in data:
            add(IssueCode.MISSING_ATTRIBUTE, "missing 'distance_nm' attribute", loc)
            continue
        value = _as_finite_float(data["distance_nm"])
        if value is None or value <= 0:
            add(IssueCode.INVALID_ATTRIBUTE, f"'distance_nm'={data['distance_nm']!r} must be a positive number", loc)

    return issues


def validate_aircraft_ids(aircraft: Iterable[Aircraft], source: str = SCENARIO_SOURCE) -> list[ValidationIssue]:
    counts = Counter(a.id for a in aircraft)
    return [
        ValidationIssue(
            code=IssueCode.DUPLICATE_AIRCRAFT_ID,
            message=f"aircraft id '{ac_id}' appears {n} times",
            source=source,
            aircraft_id=ac_id,
        )
        for ac_id, n in counts.items()
        if n > 1
    ]


def validate_flight_plan(
    plan: FlightPlan,
    index: int,
    known_aircraft_ids: set[str],
    graph: nx.Graph,
    source: str = SCENARIO_SOURCE,
) -> list[ValidationIssue]:
    """Per-plan checks (mirrors and extends the reference notebook's checks)."""
    issues: list[ValidationIssue] = []

    def add(code: IssueCode, message: str, field: str) -> None:
        issues.append(
            ValidationIssue(
                code=code,
                message=message,
                source=source,
                location=f"flight_plans[{index}].{field}",
                aircraft_id=plan.aircraft_id,
            )
        )

    if plan.aircraft_id not in known_aircraft_ids:
        add(IssueCode.UNKNOWN_AIRCRAFT, f"unknown aircraft_id: {plan.aircraft_id}", "aircraft_id")

    if len(plan.route) < 2:
        add(IssueCode.ROUTE_TOO_SHORT, "route must contain at least two waypoints", "route")
        return issues

    for node_id in plan.route:
        if node_id not in graph:
            add(IssueCode.UNKNOWN_WAYPOINT, f"unknown route waypoint: {node_id}", "route")

    for u, v in zip(plan.route[:-1], plan.route[1:]):
        if u in graph and v in graph and not graph.has_edge(u, v):
            add(IssueCode.MISSING_EDGE, f"missing directed graph edge: {u} -> {v}", "route")

    return issues


def duplicate_flight_plan_issues(
    flight_plans: list[FlightPlan], source: str = SCENARIO_SOURCE
) -> list[ValidationIssue]:
    """One flight plan per aircraft is assumed (the notebook silently overwrote duplicates)."""
    counts = Counter(p.aircraft_id for p in flight_plans)
    return [
        ValidationIssue(
            code=IssueCode.DUPLICATE_FLIGHT_PLAN,
            message=f"aircraft '{ac_id}' has {n} flight plans; exactly one is supported",
            source=source,
            aircraft_id=ac_id,
        )
        for ac_id, n in counts.items()
        if n > 1
    ]


def validate_scenario(
    aircraft: list[Aircraft],
    flight_plans: list[FlightPlan],
    graph: nx.Graph,
    source: str = SCENARIO_SOURCE,
) -> list[ValidationIssue]:
    """Run all cross-file checks and return every issue found (never raises)."""
    issues = validate_aircraft_ids(aircraft, source)
    if not flight_plans:
        issues.append(ValidationIssue(code=IssueCode.EMPTY_INPUT, message="no flight plans supplied", source=source))
    issues.extend(duplicate_flight_plan_issues(flight_plans, source))
    known = {a.id for a in aircraft}
    for i, plan in enumerate(flight_plans):
        issues.extend(validate_flight_plan(plan, i, known, graph, source))
    return issues
