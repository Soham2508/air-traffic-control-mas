"""Deterministic, trajectory-based conflict detection.

Ported from ``notebooks/reference/ConflictDetection.ipynb``. The notebook is
kept as a reference only; nothing here imports or executes it.

Model assumptions (unchanged from the reference):

* Constant speed (``Aircraft.speed_kt``) along the whole route.
* Constant altitude (``FlightPlan.cruise_altitude_ft``) for the whole plan.
* Straight-line segments between waypoints in a local equirectangular
  projection centred on the mean latitude/longitude of **all** graph nodes.
* Segment *travel time* uses the edge attribute ``distance_nm``, whereas
  *positions* use projected node coordinates. These two distances are not
  reconciled (in the sample graph ``distance_nm`` = 30 NM while the projected
  A-B distance is ~22.6 NM). This is intentional to preserve reference
  behaviour; see ``docs/architecture.md``.
* Each pair of time-overlapping segments is evaluated at its closest
  horizontal approach; a conflict is reported when horizontal distance
  ``<=`` lateral threshold **and** vertical distance ``<=`` vertical threshold
  at that same time.
* Reported values are rounded (time 3 dp, horizontal 3 dp, vertical 1 dp);
  threshold comparisons use the unrounded values.

Intentional differences from the notebook (documented and tested):

* Validation problems are returned as structured ``validation_issues`` (the
  notebook collected them in a local list and discarded them).
* Duplicate flight plans for one aircraft are reported as an issue (the
  notebook silently kept only the last one).
* Graph attribute problems are reported instead of raising ``KeyError``.

Plans that fail validation are excluded from trajectory building (as in the
notebook), but the result is then marked ``is_valid == False``.

This module has no CrewAI or LLM dependency.
"""

from __future__ import annotations

import math
from itertools import combinations

import networkx as nx

from atc_mas.config import DEFAULT_SEPARATION_MINIMA, SeparationMinima
from atc_mas.models import (
    Aircraft,
    Conflict,
    ConflictDetectionResult,
    FlightPlan,
    Scenario,
    TrajectoryPoint,
)
from atc_mas.validation import (
    duplicate_flight_plan_issues,
    validate_aircraft_ids,
    validate_airspace_graph,
    validate_flight_plan,
)

SECONDS_PER_HOUR = 3600.0
NM_PER_DEGREE_LATITUDE = 60.0


def projection_origin(graph: nx.Graph) -> tuple[float, float]:
    """Mean (lat, lon) of all graph nodes, used as the projection origin."""
    latitudes = [float(d["latitude"]) for _, d in graph.nodes(data=True)]
    longitudes = [float(d["longitude"]) for _, d in graph.nodes(data=True)]
    return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)


def project_to_local_nm(latitude: float, longitude: float, lat0: float, lon0: float) -> tuple[float, float]:
    """Simple equirectangular projection to local (x, y) in nautical miles."""
    x_nm = (longitude - lon0) * NM_PER_DEGREE_LATITUDE * math.cos(math.radians(lat0))
    y_nm = (latitude - lat0) * NM_PER_DEGREE_LATITUDE
    return x_nm, y_nm


def build_trajectory(plan: FlightPlan, aircraft: Aircraft, graph: nx.Graph) -> list[TrajectoryPoint]:
    """Build the waypoint-timed trajectory for a *validated* flight plan."""
    lat0, lon0 = projection_origin(graph)
    trajectory: list[TrajectoryPoint] = []
    current_time = plan.departure_time_s

    for i, node_id in enumerate(plan.route):
        node = graph.nodes[node_id]
        x_nm, y_nm = project_to_local_nm(float(node["latitude"]), float(node["longitude"]), lat0, lon0)
        trajectory.append(
            TrajectoryPoint(
                node_id=node_id,
                time_s=current_time,
                x_nm=x_nm,
                y_nm=y_nm,
                altitude_ft=plan.cruise_altitude_ft,
            )
        )
        if i < len(plan.route) - 1:
            distance_nm = float(graph[node_id][plan.route[i + 1]]["distance_nm"])
            current_time += distance_nm / aircraft.speed_kt * SECONDS_PER_HOUR

    return trajectory


def position_at(p0: TrajectoryPoint, p1: TrajectoryPoint, time_s: float) -> tuple[float, float, float]:
    """Linear interpolation of (x_nm, y_nm, altitude_ft) between two points."""
    if abs(p1.time_s - p0.time_s) < 1e-9:
        ratio = 0.0
    else:
        ratio = (time_s - p0.time_s) / (p1.time_s - p0.time_s)
    x = p0.x_nm + ratio * (p1.x_nm - p0.x_nm)
    y = p0.y_nm + ratio * (p1.y_nm - p0.y_nm)
    altitude = p0.altitude_ft + ratio * (p1.altitude_ft - p0.altitude_ft)
    return x, y, altitude


def closest_approach(
    a0: TrajectoryPoint,
    a1: TrajectoryPoint,
    b0: TrajectoryPoint,
    b1: TrajectoryPoint,
    t0: float,
    t1: float,
) -> tuple[float, float, float]:
    """Closest horizontal approach of two segments over the overlap ``[t0, t1]``.

    Returns ``(time_s, horizontal_distance_nm, vertical_distance_ft)``.
    """
    candidates = [t0, t1]

    ax0, ay0, _ = position_at(a0, a1, t0)
    bx0, by0, _ = position_at(b0, b1, t0)
    ax1, ay1, _ = position_at(a0, a1, t1)
    bx1, by1, _ = position_at(b0, b1, t1)

    rx0, ry0 = ax0 - bx0, ay0 - by0
    rx1, ry1 = ax1 - bx1, ay1 - by1
    vx, vy = rx1 - rx0, ry1 - ry0

    denominator = vx * vx + vy * vy
    if denominator > 1e-12:
        u = -((rx0 * vx) + (ry0 * vy)) / denominator
        if 0.0 <= u <= 1.0:
            candidates.append(t0 + u * (t1 - t0))

    best_time = candidates[0]
    best_horizontal = math.inf
    best_vertical = math.inf
    for t in candidates:
        ax, ay, aa = position_at(a0, a1, t)
        bx, by, ba = position_at(b0, b1, t)
        horizontal = math.hypot(ax - bx, ay - by)
        if horizontal < best_horizontal:
            best_time, best_horizontal, best_vertical = t, horizontal, abs(aa - ba)

    return best_time, best_horizontal, best_vertical


def detect_conflicts(
    aircraft_list: list[Aircraft],
    flight_plans: list[FlightPlan],
    graph: nx.Graph,
    separation_minima: SeparationMinima = DEFAULT_SEPARATION_MINIMA,
) -> ConflictDetectionResult:
    """Detect all pairwise separation conflicts.

    Args:
        aircraft_list: Aircraft records.
        flight_plans: One flight plan per aircraft.
        graph: Directed airspace graph (see :func:`atc_mas.io.load_airspace_graph`).
        separation_minima: Thresholds; defaults to the single configured source.

    Returns:
        A :class:`ConflictDetectionResult`. Check ``is_valid`` before
        interpreting a zero ``conflict_count``.
    """
    graph_issues = validate_airspace_graph(graph)
    if graph_issues:
        return ConflictDetectionResult(validation_issues=graph_issues, separation_minima=separation_minima)

    issues = validate_aircraft_ids(aircraft_list)
    duplicate_plan_issues = duplicate_flight_plan_issues(flight_plans)
    issues.extend(duplicate_plan_issues)
    duplicated = {i.aircraft_id for i in duplicate_plan_issues}

    aircraft_by_id = {a.id: a for a in aircraft_list}
    trajectories: dict[str, list[TrajectoryPoint]] = {}
    for index, plan in enumerate(flight_plans):
        plan_issues = validate_flight_plan(plan, index, set(aircraft_by_id), graph)
        issues.extend(plan_issues)
        if not plan_issues and plan.aircraft_id not in duplicated:
            trajectories[plan.aircraft_id] = build_trajectory(plan, aircraft_by_id[plan.aircraft_id], graph)

    conflicts: list[Conflict] = []
    lateral = separation_minima.lateral_threshold_nm
    vertical = separation_minima.vertical_threshold_ft

    for ac1, ac2 in combinations(sorted(trajectories), 2):
        traj1, traj2 = trajectories[ac1], trajectories[ac2]
        for p1_start, p1_end in zip(traj1[:-1], traj1[1:]):
            for p2_start, p2_end in zip(traj2[:-1], traj2[1:]):
                overlap_start = max(p1_start.time_s, p2_start.time_s)
                overlap_end = min(p1_end.time_s, p2_end.time_s)
                if overlap_start > overlap_end:
                    continue
                time_s, horizontal_nm, vertical_ft = closest_approach(
                    p1_start, p1_end, p2_start, p2_end, overlap_start, overlap_end
                )
                if horizontal_nm <= lateral and vertical_ft <= vertical:
                    conflicts.append(
                        Conflict(
                            aircraft_1=ac1,
                            aircraft_2=ac2,
                            time_s=round(time_s, 3),
                            horizontal_distance_nm=round(horizontal_nm, 3),
                            vertical_distance_ft=round(vertical_ft, 1),
                            segment_1=[p1_start.node_id, p1_end.node_id],
                            segment_2=[p2_start.node_id, p2_end.node_id],
                        )
                    )

    return ConflictDetectionResult(
        conflicts=conflicts,
        validation_issues=issues,
        separation_minima=separation_minima,
        analysed_aircraft_ids=sorted(trajectories),
    )


def detect_conflicts_in_scenario(
    scenario: Scenario, separation_minima: SeparationMinima = DEFAULT_SEPARATION_MINIMA
) -> ConflictDetectionResult:
    """Convenience wrapper for a loaded :class:`Scenario`."""
    return detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph, separation_minima)
