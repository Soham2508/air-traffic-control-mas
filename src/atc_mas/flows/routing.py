"""Pure routing decision used by the ATC Flow router (no CrewAI import)."""

from __future__ import annotations

from enum import Enum

from atc_mas.models import ConflictDetectionResult


class Route(str, Enum):
    """Router outcomes. Values are the CrewAI Flow event names."""

    CONFLICTS_DETECTED = "conflicts_detected"
    NO_CONFLICTS = "no_conflicts"
    INVALID_INPUT = "invalid_input"


def decide_route(detection: ConflictDetectionResult) -> Route:
    """Decide the next stage from **structured** detection data only.

    * Invalid/incomplete input → ``INVALID_INPUT`` (straight to Reporting; the
      report is marked invalid and tactical resolution is not attempted on an
      incomplete traffic picture).
    * Any conflict → ``CONFLICTS_DETECTED`` (Tactical Resolution, then Reporting).
    * Otherwise → ``NO_CONFLICTS`` (straight to Reporting).
    """
    if not detection.is_valid:
        return Route.INVALID_INPUT
    if detection.has_conflicts:
        return Route.CONFLICTS_DETECTED
    return Route.NO_CONFLICTS
