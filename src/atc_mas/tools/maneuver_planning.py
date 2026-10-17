"""Tactical maneuver planning — **placeholder**.

No maneuver algorithm exists yet. Every proposal is ``NOT_IMPLEMENTED`` and
must never be reported as a safe or validated resolution.

TODO(task-2): generate candidate maneuvers (altitude change, delay, re-route),
then re-run ``detect_conflicts`` on the modified scenario before marking any
proposal ``VALIDATED``.
"""

from __future__ import annotations

from atc_mas.models import Conflict, ResolutionProposal, ResolutionStatus


def propose_resolutions(conflicts: list[Conflict]) -> list[ResolutionProposal]:
    """Return one ``NOT_IMPLEMENTED`` proposal per conflict."""
    return [
        ResolutionProposal(
            conflict=conflict,
            status=ResolutionStatus.NOT_IMPLEMENTED,
            summary="Maneuver planning not implemented; conflict remains unresolved.",
        )
        for conflict in conflicts
    ]
