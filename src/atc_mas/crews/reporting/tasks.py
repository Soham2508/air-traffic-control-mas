"""Tasks for the Reporting Crew.

Input interpolated at ``kickoff``: ``analysis_json`` (``ATCAnalysis`` as JSON).
"""

from __future__ import annotations

from crewai import Agent, Task


def create_summary_task(agent: Agent) -> Task:
    return Task(
        description=(
            "Here is the structured ATC analysis as JSON:\n\n{analysis_json}\n\n"
            "Write a 1-3 paragraph executive summary covering: overall analysis_status, input "
            "validity, number of conflicts and the aircraft involved, and the status of any "
            "resolutions. Copy status values verbatim. State that this is a simulation and not a "
            "clearance."
        ),
        expected_output="A short Markdown executive summary.",
        agent=agent,
    )
