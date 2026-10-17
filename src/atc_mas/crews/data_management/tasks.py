"""Tasks for Data Management Crew."""

from __future__ import annotations

from crewai import Agent, Task


def create_validate_inputs_task(agent: Agent) -> Task:
    return Task(
        description="Verify scenario files: '{airspace_path}', '{aircraft_path}', '{flight_plans_path}'.",
        expected_output="Summary of scenario data verification.",
        agent=agent,
    )
