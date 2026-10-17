"""Agents for the Surveillance & Conflict Crew."""

from __future__ import annotations

from typing import Any

from crewai import Agent

from atc_mas.crews.common import agent_llm_kwargs
from atc_mas.tools.crewai_tools import ConflictDetectionTool


def create_conflict_analyst_agent(llm: Any | None = None) -> Agent:
    """Agent that runs the deterministic detector and interprets its output."""
    return Agent(
        role="Surveillance and Conflict Analyst",
        goal=(
            "Run the deterministic conflict-detection tool and explain the detected separation "
            "conflicts accurately, using only the numbers the tool returns."
        ),
        backstory=(
            "You monitor simulated traffic for losses of separation. All distances and times come "
            "from the deterministic tool; you never compute or estimate them yourself."
        ),
        tools=[ConflictDetectionTool()],
        allow_delegation=False,
        verbose=False,
        **agent_llm_kwargs(llm),
    )
