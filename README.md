# Air Traffic Control Multi-Agent System (ATC-MAS)

Initial repository scaffold for the URV Multi-Agent Systems practical work on Air Traffic Control Conflict Detection and Resolution.

---

## 1. Project Overview

The ATC-MAS system processes batch flight scenarios across a directed airspace graph. Its purpose is to:
1. Load and validate airspace structures (GraphML), aircraft performance, and flight plans (JSON).
2. Compute 4D aircraft trajectories and detect separation minimum violations (5.0 NM horizontal, 1,000 ft vertical) using deterministic trajectory calculations.
3. Coordinate multi-agent flows (CrewAI) with conditional routing: scenarios with conflicts route to Tactical Resolution, while conflict-free scenarios route directly to Reporting.
4. Output structured analysis artifacts (`.json`) and human-readable Markdown ATC reports (`.md`).

---

## 2. Repository Layout

```text
atc-mas/
├── README.md                          # Project documentation and usage
├── pyproject.toml                     # Project packaging and dependencies
├── .gitignore                         # Git ignore definitions
├── .env.example                       # Environment configuration template
├── data/
│   ├── input/                         # Supplied input files
│   │   ├── sample_airspace.graphml
│   │   ├── sample_aircraft.json
│   │   ├── sample_conflict_flight_plans.json
│   │   ├── sample_no_conflict_flight_plans.json
│   │   └── sample_conflict_2_flight_plans.json
│   └── output/                        # Generated output JSON and reports
├── docs/
│   └── architecture.md                # System design and component roles
├── notebooks/
│   └── reference/
│       └── ConflictDetection.ipynb    # Preserved original reference notebook
├── src/
│   └── atc_mas/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py                     # CLI entry point
│       ├── config.py                  # Single source of truth for thresholds
│       ├── models.py                  # Shared Pydantic domain models
│       ├── pipeline.py                # Deterministic execution pipeline
│       ├── validation.py              # Input schema and cross-file validation
│       ├── io/
│       │   ├── __init__.py
│       │   └── loaders.py             # Robust GraphML & JSON loaders
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── conflict_detection.py  # Pure trajectory conflict detection
│       │   ├── maneuver_planning.py   # Placeholder tactical maneuver planner
│       │   └── crewai_tools.py        # CrewAI BaseTool adapter
│       ├── crews/
│       │   ├── common.py
│       │   ├── data_management/       # Data Steward agent & crew
│       │   ├── surveillance_conflict/ # Conflict Analyst agent & crew
│       │   ├── tactical_resolution/   # Maneuver Planner agent & crew (Stub)
│       │   └── reporting/             # Report Writer agent & crew
│       ├── flows/
│       │   ├── routing.py             # Pure routing logic
│       │   └── atc_flow.py            # CrewAI Flow with conditional branch
│       └── reporting/
│           ├── __init__.py
│           └── markdown_report.py     # Deterministic Markdown report renderer
└── tests/
    ├── unit/
    │   ├── test_loaders.py            # Validation & loader test suite
    │   └── test_conflict_detection.py # Detection & routing tests
    └── integration/
        └── test_sample_scenarios.py   # Integration tests for sample scenarios
```

---

## 3. Installation & Setup

### Requirements
- Python 3.10 to 3.12 (Tested on Python 3.12)
- Virtual environment recommended

### Installation

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

---

## 4. Running the Deterministic CLI

No LLM API keys or credentials are required to run deterministic conflict detection.

```bash
# Run conflict detection on the 1-conflict sample scenario:
python -m atc_mas detect \
  --airspace data/input/sample_airspace.graphml \
  --aircraft data/input/sample_aircraft.json \
  --flight-plans data/input/sample_conflict_flight_plans.json \
  --output data/output/conflict_result.json \
  --report data/output/atc_report.md

# Run on the 0-conflict sample scenario:
python -m atc_mas detect \
  --airspace data/input/sample_airspace.graphml \
  --aircraft data/input/sample_aircraft.json \
  --flight-plans data/input/sample_no_conflict_flight_plans.json

# Run on the 2-conflict sample scenario:
python -m atc_mas detect \
  --airspace data/input/sample_airspace.graphml \
  --aircraft data/input/sample_aircraft.json \
  --flight-plans data/input/sample_conflict_2_flight_plans.json
```

Outputs will be saved in `data/output/`:
- `conflict_result.json`: Detailed machine-readable JSON analysis.
- `atc_report.md`: Structured Markdown ATC summary report.

---

## 5. Running Automated Tests

Run the full pytest suite (no API key required):

```bash
pytest -v
```

All 14 unit and integration tests pass cleanly, verifying:
- GraphML & JSON loading, field validation, and error reporting.
- Sample scenarios producing exactly 1, 0, and 2 conflicts as expected.
- Rejection of unknown waypoints, missing edges, duplicate aircraft IDs, and short routes.

---

## 6. Multi-Agent System Architecture & Status

| Crew / Component | Status | Description |
|---|---|---|
| **Data Management Crew** | Implemented | Validates airspace graph and flight plans |
| **Surveillance & Conflict Crew** | Implemented | Executes deterministic separation monitoring |
| **Tactical Resolution Crew** | Scaffold / Placeholder | Maneuver planning returns `NOT_IMPLEMENTED` |
| **Reporting Crew** | Implemented | Assembles structured results into reports |
| **ATC Flow & Router** | Implemented | Conditional routing based on `has_conflicts` |

### Key Assumptions & Safety Notes
- Lateral separation minimum: **5.0 NM**, Vertical separation minimum: **1,000 ft**.
- Maneuvers are **not** implemented in this initial scaffold; conflicts are accurately labeled as `UNRESOLVED`.
- Zero-conflict status is only produced if all inputs pass rigorous validation.