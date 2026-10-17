"""Deterministic analysis steps shared by the CLI and the CrewAI Flow (no LLM)."""

from __future__ import annotations

from pathlib import Path

from atc_mas.config import DEFAULT_SEPARATION_MINIMA, SeparationMinima
from atc_mas.io.loaders import InputValidationError, load_scenario
from atc_mas.models import ATCAnalysis, ConflictDetectionResult, InputFiles
from atc_mas.reporting.markdown_report import render_markdown_report
from atc_mas.tools.conflict_detection import detect_conflicts
from atc_mas.tools.maneuver_planning import propose_resolutions


def run_analysis(
    airspace: str | Path,
    aircraft: str | Path,
    flight_plans: str | Path,
    separation_minima: SeparationMinima = DEFAULT_SEPARATION_MINIMA,
) -> ATCAnalysis:
    """Load → validate → detect → placeholder resolution. Invalid input yields an INVALID result."""
    files = InputFiles(airspace=str(airspace), aircraft=str(aircraft), flight_plans=str(flight_plans))
    try:
        scenario = load_scenario(airspace, aircraft, flight_plans)
    except InputValidationError as exc:
        detection = ConflictDetectionResult(validation_issues=exc.issues, separation_minima=separation_minima)
        return ATCAnalysis(input_files=files, detection=detection)

    detection = detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph, separation_minima)
    resolutions = propose_resolutions(detection.conflicts) if detection.is_valid else []
    return ATCAnalysis(input_files=files, scenario=scenario.summary(), detection=detection, resolutions=resolutions)


def write_outputs(analysis: ATCAnalysis, json_path: str | Path, report_path: str | Path) -> None:
    """Write the structured JSON result and the Markdown report."""
    for path, text in (
        (Path(json_path), analysis.model_dump_json(indent=2) + "\n"),
        (Path(report_path), render_markdown_report(analysis)),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
