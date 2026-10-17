from pathlib import Path

import pytest

from atc_mas.io.loaders import (
    InputValidationError,
    load_aircraft,
    load_airspace_graph,
    load_flight_plans,
    load_scenario,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_INPUT = REPO_ROOT / "data" / "input"


def test_load_valid_airspace_graph():
    graph_path = DATA_INPUT / "sample_airspace.graphml"
    graph = load_airspace_graph(graph_path)
    assert graph.is_directed()
    assert "A" in graph.nodes
    assert "B" in graph.nodes
    assert "latitude" in graph.nodes["A"]
    assert "longitude" in graph.nodes["A"]
    assert graph.has_edge("A", "B")
    assert "distance_nm" in graph["A"]["B"]


def test_load_valid_aircraft():
    aircraft_path = DATA_INPUT / "sample_aircraft.json"
    aircraft = load_aircraft(aircraft_path)
    assert len(aircraft) == 2
    ids = {a.id for a in aircraft}
    assert "AC1" in ids and "AC2" in ids
    assert aircraft[0].speed_kt > 0


def test_load_valid_flight_plans():
    plans_path = DATA_INPUT / "sample_conflict_flight_plans.json"
    plans = load_flight_plans(plans_path)
    assert len(plans) == 2
    assert len(plans[0].route) >= 2


def test_load_scenario_valid():
    scenario = load_scenario(
        DATA_INPUT / "sample_airspace.graphml",
        DATA_INPUT / "sample_aircraft.json",
        DATA_INPUT / "sample_conflict_flight_plans.json",
    )
    assert len(scenario.aircraft) == 2
    assert len(scenario.flight_plans) == 2


def test_missing_file_raises_validation_error(tmp_path):
    with pytest.raises(InputValidationError) as exc_info:
        load_aircraft(tmp_path / "non_existent.json")
    assert any(i.code.value == "FILE_NOT_FOUND" for i in exc_info.value.issues)


def test_malformed_json_raises_validation_error(tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ broken json", encoding="utf-8")
    with pytest.raises(InputValidationError) as exc_info:
        load_aircraft(bad_json)
    assert any(i.code.value == "INVALID_FORMAT" for i in exc_info.value.issues)


def test_duplicate_aircraft_id_rejected(tmp_path):
    dupes = tmp_path / "dupe_ac.json"
    dupes.write_text('[{"id": "AC1", "speed_kt": 400}, {"id": "AC1", "speed_kt": 450}]', encoding="utf-8")
    with pytest.raises(InputValidationError) as exc_info:
        load_aircraft(dupes)
    assert any(i.code.value == "DUPLICATE_AIRCRAFT_ID" for i in exc_info.value.issues)


def test_unknown_aircraft_in_flight_plan(tmp_path):
    bad_plan = tmp_path / "bad_plan.json"
    bad_plan.write_text('[{"aircraft_id": "UNKNOWN_99", "route": ["A", "B"], "departure_time_s": 0.0, "cruise_altitude_ft": 30000}]', encoding="utf-8")
    with pytest.raises(InputValidationError) as exc_info:
        load_scenario(
            DATA_INPUT / "sample_airspace.graphml",
            DATA_INPUT / "sample_aircraft.json",
            bad_plan,
        )
    assert any(i.code.value == "UNKNOWN_AIRCRAFT" for i in exc_info.value.issues)


def test_route_too_short_rejected(tmp_path):
    short_route = tmp_path / "short_route.json"
    short_route.write_text('[{"aircraft_id": "AC1", "route": ["A"], "departure_time_s": 0.0, "cruise_altitude_ft": 30000}]', encoding="utf-8")
    with pytest.raises(InputValidationError) as exc_info:
        load_scenario(
            DATA_INPUT / "sample_airspace.graphml",
            DATA_INPUT / "sample_aircraft.json",
            short_route,
        )
    assert any(i.code.value == "ROUTE_TOO_SHORT" for i in exc_info.value.issues)

