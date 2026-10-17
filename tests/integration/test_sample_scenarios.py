from pathlib import Path
from atc_mas.io.loaders import load_scenario
from atc_mas.tools.conflict_detection import detect_conflicts

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_INPUT = REPO_ROOT / "data" / "input"


def test_scenario_sample_conflict_flight_plans():
    """Requirement: sample_conflict_flight_plans.json must yield exactly 1 conflict."""
    scenario = load_scenario(
        DATA_INPUT / "sample_airspace.graphml",
        DATA_INPUT / "sample_aircraft.json",
        DATA_INPUT / "sample_conflict_flight_plans.json",
    )
    result = detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph)
    assert result.is_valid
    assert result.conflict_count == 1
    conflict = result.conflicts[0]
    assert conflict.aircraft_1 == "AC1"
    assert conflict.aircraft_2 == "AC2"
    assert conflict.time_s == 112.5
    assert conflict.horizontal_distance_nm == 0.0
    assert conflict.vertical_distance_ft == 0.0


def test_scenario_sample_no_conflict_flight_plans():
    """Requirement: sample_no_conflict_flight_plans.json must yield exactly 0 conflicts."""
    scenario = load_scenario(
        DATA_INPUT / "sample_airspace.graphml",
        DATA_INPUT / "sample_aircraft.json",
        DATA_INPUT / "sample_no_conflict_flight_plans.json",
    )
    result = detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph)
    assert result.is_valid
    assert result.conflict_count == 0


def test_scenario_sample_conflict_2_flight_plans():
    """Requirement: sample_conflict_2_flight_plans.json must yield exactly 2 conflicts."""
    scenario = load_scenario(
        DATA_INPUT / "sample_airspace.graphml",
        DATA_INPUT / "sample_aircraft.json",
        DATA_INPUT / "sample_conflict_2_flight_plans.json",
    )
    result = detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph)
    assert result.is_valid
    assert result.conflict_count == 2
    times = [c.time_s for c in result.conflicts]
    assert times == [112.5, 337.5]

