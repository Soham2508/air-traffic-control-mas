"""Agents for the Data Management Crew."""

from __future__ import annotations

from typing import Any

from crewai import Agent

from atc_mas.crews.common import agent_llm_kwargs


def create_data_steward_agent(llm: Any | None = None) -> Agent:
    """Agent that handles input scenario data."""
    return Agent(
        role="Airspace Data Steward",
        goal="Validate and report on airspace, aircraft, and flight plan data.",
        backstory="You prepare and inspect flight scenarios for the simulated ATC system.",
        allow_delegation=False,
        verbose=False,
        **agent_llm_kwargs(llm),
    )
