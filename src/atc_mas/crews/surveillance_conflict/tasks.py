"""Tasks for the Surveillance & Conflict Crew.

Inputs interpolated at ``kickoff``: ``airspace_path``, ``aircraft_path``,
``flight_plans_path``.
"""

from __future__ import annotations

from crewai import Agent, Task


def create_assess_conflicts_task(agent: Agent) -> Task:
    # NOTE: the Flow routes on the deterministic ConflictDetectionResult, never on this text.
    return Task(
        description=(
            "Call the detect_conflicts tool with airspace_path='{airspace_path}', "
            "aircraft_path='{aircraft_path}' and flight_plans_path='{flight_plans_path}'. "
            "If 'is_valid' is false, say the analysis is incomplete and list the issues. "
            "Otherwise report the conflict count and, for each conflict, the aircraft pair, "
            "time, horizontal and vertical separation, and segments, exactly as returned."
        ),
        expected_output="A short, factual Markdown summary of the tool's ConflictDetectionResult.",
        agent=agent,
    )
