"""Tactical Resolution Crew assembly (INCOMPLETE)."""

from __future__ import annotations

from typing import Any

from crewai import Crew, Process

from atc_mas.crews.tactical_resolution.agents import (
    create_maneuver_planner_agent,
    create_resolution_validator_agent,
)
from atc_mas.crews.tactical_resolution.tasks import (
    create_propose_maneuvers_task,
    create_validate_maneuvers_task,
)


def build_tactical_resolution_crew(llm: Any | None = None) -> Crew:
    """Build (but do not run) the Tactical Resolution Crew."""
    planner = create_maneuver_planner_agent(llm)
    validator = create_resolution_validator_agent(llm)
    propose = create_propose_maneuvers_task(planner)
    return Crew(
        agents=[planner, validator],
        tasks=[propose, create_validate_maneuvers_task(validator, propose)],
        process=Process.sequential,
        verbose=False,
    )
