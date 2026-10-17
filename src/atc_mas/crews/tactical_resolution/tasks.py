"""Tasks for the Tactical Resolution Crew (placeholder)."""

from __future__ import annotations

from crewai import Agent, Task


def create_propose_maneuvers_task(agent: Agent) -> Task:
    return Task(
        description="Review conflicts for scenario and record placeholder resolution proposals (NOT_IMPLEMENTED).",
        expected_output="List of unresolved conflict notices marked NOT_IMPLEMENTED.",
        agent=agent,
    )


def create_validate_maneuvers_task(agent: Agent, proposals_task: Task) -> Task:
    return Task(
        description="Verify status of proposals. Confirm that unresolved conflicts remain unvalidated.",
        expected_output="Validation summary verifying all proposals remain unresolved.",
        agent=agent,
        context=[proposals_task],
    )
