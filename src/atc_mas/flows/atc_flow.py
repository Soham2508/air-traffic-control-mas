"""CrewAI Flow orchestrating the ATC Conflict Detection and Resolution pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel, Field

from atc_mas.config import DEFAULT_SEPARATION_MINIMA, SeparationMinima
from atc_mas.flows.routing import Route, decide_route
from atc_mas.models import ATCAnalysis
from atc_mas.pipeline import run_analysis, write_outputs


class ATCState(BaseModel):
    """Flow state for ATC batch execution."""

    airspace_path: str = ""
    aircraft_path: str = ""
    flight_plans_path: str = ""
    output_json_path: str = "data/output/conflict_result.json"
    output_report_path: str = "data/output/atc_report.md"
    separation_minima: SeparationMinima = Field(default_factory=SeparationMinima)
    analysis: ATCAnalysis | None = None
    route: str = ""


class ATCFlow(Flow[ATCState]):
    """ATC Flow coordinating detection, conditional tactical resolution, and reporting."""

    initial_state = ATCState

    @start()
    def detect_conflicts_step(self) -> None:
        """Run deterministic validation and conflict detection."""
        self.state.analysis = run_analysis(
            airspace=self.state.airspace_path,
            aircraft=self.state.aircraft_path,
            flight_plans=self.state.flight_plans_path,
            separation_minima=self.state.separation_minima,
        )

    @router(detect_conflicts_step)
    def route_conflicts(self) -> str:
        """Route conditionally based on structured ConflictDetectionResult."""
        if self.state.analysis is None:
            return Route.INVALID_INPUT.value

        decision = decide_route(self.state.analysis.detection)
        self.state.route = decision.value
        return decision.value

    @listen(Route.CONFLICTS_DETECTED.value)
    def tactical_resolution_step(self) -> None:
        """Route when conflicts are detected: tactical resolution placeholder."""
        # Tactical resolution placeholder: already marked NOT_IMPLEMENTED in analysis
        pass

    @listen(or_(Route.NO_CONFLICTS.value, Route.INVALID_INPUT.value, tactical_resolution_step))
    def reporting_step(self) -> ATCAnalysis:
        """Generate final outputs (JSON and Markdown report)."""
        if self.state.analysis is not None:
            write_outputs(
                analysis=self.state.analysis,
                json_path=self.state.output_json_path,
                report_path=self.state.output_report_path,
            )
        return self.state.analysis

