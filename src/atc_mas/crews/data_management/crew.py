"""Data Management Crew assembly."""

from __future__ import annotations

from typing import Any

from crewai import Crew, Process

from atc_mas.crews.data_management.agents import create_data_steward_agent
from atc_mas.crews.data_management.tasks import create_validate_inputs_task


def build_data_management_crew(llm: Any | None = None) -> Crew:
    """Build (but do not run) the Data Management Crew."""
    steward = create_data_steward_agent(llm)
    return Crew(
        agents=[steward],
        tasks=[create_validate_inputs_task(steward)],
        process=Process.sequential,
        verbose=False,
    )
