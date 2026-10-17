"""Tactical Resolution Crew — **INCOMPLETE in this scaffold**.

Exposes the intended proposal and validation agents/tasks. The underlying
maneuver planner returns ``NOT_IMPLEMENTED``; nothing produced here may be
treated as a safe or validated resolution.
"""

from atc_mas.crews.tactical_resolution.crew import build_tactical_resolution_crew

__all__ = ["build_tactical_resolution_crew"]
