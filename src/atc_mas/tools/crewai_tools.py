"""CrewAI BaseTool wrapper around the deterministic conflict detection."""

from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from atc_mas.pipeline import run_analysis


class ScenarioPathsInput(BaseModel):
    airspace_path: str = Field(..., description="Path to airspace GraphML file")
    aircraft_path: str = Field(..., description="Path to aircraft JSON file")
    flight_plans_path: str = Field(..., description="Path to flight plans JSON file")


class ConflictDetectionTool(BaseTool):
    name: str = "detect_conflicts"
    description: str = "Run deterministic conflict detection on airspace, aircraft, and flight plans."
    args_schema: type[BaseModel] = ScenarioPathsInput

    def _run(self, airspace_path: str, aircraft_path: str, flight_plans_path: str) -> str:
        return run_analysis(airspace_path, aircraft_path, flight_plans_path).model_dump_json(indent=2)
