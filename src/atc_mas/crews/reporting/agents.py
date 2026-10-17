"""Agents for the Reporting Crew."""

from __future__ import annotations

from typing import Any

from crewai import Agent

from atc_mas.crews.common import agent_llm_kwargs


def create_report_writer_agent(llm: Any | None = None) -> Agent:
    return Agent(
        role="ATC Report Writer",
        goal=(
            "Write a clear executive summary of the structured ATC analysis JSON without changing "
            "any number or status."
        ),
        backstory=(
            "You write briefings for a simulated ATC exercise. You copy statuses such as "
            "INVALID_INPUT, CONFLICTS_UNRESOLVED and NOT_IMPLEMENTED verbatim, never claim a "
            "conflict is resolved unless a proposal is VALIDATED, and never issue clearances."
        ),
        allow_delegation=False,
        verbose=False,
        **agent_llm_kwargs(llm),
    )
