"""Reporting Crew assembly.

The authoritative Markdown report is rendered deterministically by
:mod:`atc_mas.reporting.markdown_report`; this crew only adds an optional,
clearly labelled narrative appendix.
"""

from __future__ import annotations

from typing import Any

from crewai import Crew, Process

from atc_mas.crews.reporting.agents import create_report_writer_agent
from atc_mas.crews.reporting.tasks import create_summary_task


def build_reporting_crew(llm: Any | None = None) -> Crew:
    """Build (but do not run) the Reporting Crew."""
    writer = create_report_writer_agent(llm)
    return Crew(
        agents=[writer],
        tasks=[create_summary_task(writer)],
        process=Process.sequential,
        verbose=False,
    )
