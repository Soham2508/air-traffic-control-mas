"""Surveillance & Conflict Crew assembly."""

from __future__ import annotations

from typing import Any

from crewai import Crew, Process

from atc_mas.crews.surveillance_conflict.agents import create_conflict_analyst_agent
from atc_mas.crews.surveillance_conflict.tasks import create_assess_conflicts_task


def build_surveillance_conflict_crew(llm: Any | None = None) -> Crew:
    """Build (but do not run) the Surveillance & Conflict Crew."""
    analyst = create_conflict_analyst_agent(llm)
    return Crew(
        agents=[analyst],
        tasks=[create_assess_conflicts_task(analyst)],
        process=Process.sequential,
        verbose=False,
    )
