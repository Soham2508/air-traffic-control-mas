from pathlib import Path

from atc_mas.flows.routing import Route, decide_route
from atc_mas.io.loaders import load_scenario
from atc_mas.tools.conflict_detection import detect_conflicts

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_INPUT = REPO_ROOT / "data" / "input"


def test_conflict_detection_one_conflict():
    scenario = load_scenario(
        DATA_INPUT / "sample_airspace.graphml",
        DATA_INPUT / "sample_aircraft.json",
        DATA_INPUT / "sample_conflict_flight_plans.json",
    )
    res = detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph)
    assert res.is_valid
    assert res.has_conflicts
    assert res.conflict_count == 1
    assert decide_route(res) == Route.CONFLICTS_DETECTED


def test_conflict_detection_no_conflict():
    scenario = load_scenario(
        DATA_INPUT / "sample_airspace.graphml",
        DATA_INPUT / "sample_aircraft.json",
        DATA_INPUT / "sample_no_conflict_flight_plans.json",
    )
    res = detect_conflicts(scenario.aircraft, scenario.flight_plans, scenario.graph)
    assert res.is_valid
    assert not res.has_conflicts
    assert res.conflict_count == 0
    assert decide_route(res) == Route.NO_CONFLICTS

