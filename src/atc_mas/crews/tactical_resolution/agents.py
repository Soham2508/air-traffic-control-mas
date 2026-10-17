"""Agents for the Tactical Resolution Crew (placeholder scaffold)."""

from __future__ import annotations

from typing import Any

from crewai import Agent

from atc_mas.crews.common import agent_llm_kwargs


def create_maneuver_planner_agent(llm: Any | None = None) -> Agent:
    return Agent(
        role="Tactical Maneuver Planner",
        goal="Propose tactical resolution maneuvers (placeholder in this scaffold).",
        backstory="Plans potential resolution maneuvers. Tactical resolution is not implemented in this scaffold.",
        allow_delegation=False,
        verbose=False,
        **agent_llm_kwargs(llm),
    )


def create_resolution_validator_agent(llm: Any | None = None) -> Agent:
    return Agent(
        role="Resolution Safety Validator",
        goal="Verify safety of proposed maneuvers. Rejects any unvalidated proposals.",
        backstory="Validates resolution maneuvers against separation criteria.",
        allow_delegation=False,
        verbose=False,
        **agent_llm_kwargs(llm),
    )
