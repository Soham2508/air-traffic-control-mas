"""Markdown rendering of an :class:`~atc_mas.models.ATCAnalysis`.

The renderer only reads structured data. It never upgrades a status: a
conflict is described as resolved only when the overall status is
``CONFLICTS_RESOLVED_VALIDATED``, which requires a ``VALIDATED`` proposal.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from atc_mas.models import AnalysisStatus, ATCAnalysis, ResolutionStatus

STATUS_EXPLANATIONS: dict[AnalysisStatus, str] = {
    AnalysisStatus.INVALID_INPUT: (
        "**Analysis INVALID / INCOMPLETE.** Input validation failed. Any conflict count shown "
        "is not meaningful and must not be read as 'no conflicts'. Fix the issues listed in "
        "Section 2 and re-run."
    ),
    AnalysisStatus.NO_CONFLICTS_DETECTED: (
        "No separation conflicts were detected for the validated inputs under the stated model "
        "assumptions and thresholds."
    ),
    AnalysisStatus.CONFLICTS_UNRESOLVED: (
        "**Conflicts detected and UNRESOLVED.** No validated tactical resolution is available "
        "(maneuver planning is not implemented in this scaffold)."
    ),
    AnalysisStatus.CONFLICTS_RESOLVED_VALIDATED: (
        "Conflicts were detected and at least one proposed resolution passed a full-scenario "
        "deterministic re-check with zero remaining conflicts."
    ),
}

ASSUMPTIONS = [
    "Constant speed (`speed_kt`) along the whole route.",
    "Constant altitude (`cruise_altitude_ft`) for each flight plan; no climb/descent.",
    "Straight-line segments in a local equirectangular projection centred on the mean node position.",
    "Segment travel time uses edge `distance_nm`; positions use projected node coordinates "
    "(these distances are not reconciled).",
    "Each time-overlapping segment pair is evaluated at its closest horizontal approach.",
    "No wind, weather, aircraft performance limits, or surveillance uncertainty is modelled.",
]

LIMITATIONS = [
    "Academic batch simulation only; not a certified or operational ATC system.",
    "This report is **not an ATC clearance** and must not be used for real-world operations.",
    "Tactical maneuver planning is a placeholder (`NOT_IMPLEMENTED`).",
    "Conflicts are reported per overlapping segment pair, so one encounter can appear more than once.",
]


def _row(*cells: object) -> str:
    return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"


def _fmt(value: float) -> str:
    return f"{value:g}"


def render_markdown_report(
    analysis: ATCAnalysis,
    *,
    generated_at: datetime | None = None,
    llm_summary: str | None = None,
) -> str:
    """Render the full Markdown report."""
    det = analysis.detection
    status = analysis.analysis_status
    generated_at = generated_at or datetime.now(timezone.utc)
    files = analysis.input_files
    out: list[str] = []
    add = out.append

    add("# ATC Conflict Detection & Resolution Report (Simulation)")
    add("")
    add("> [!CAUTION]")
    add("> Simulated academic result. **Not a real ATC clearance.**")
    add("")

    # 1. Run summary --------------------------------------------------------
    add("## 1. Run summary")
    add("")
    add(_row("Item", "Value"))
    add(_row("---", "---"))
    add(_row("Analysis status", f"`{status.value}`"))
    add(_row("Inputs valid", "yes" if det.is_valid else "**NO**"))
    add(_row("Conflicts detected", det.conflict_count))
    add(_row("Aircraft analysed", ", ".join(det.analysed_aircraft_ids) or "none"))
    add(_row("Airspace file", f"`{Path(files.airspace).name}` (`{files.airspace}`)"))
    add(_row("Aircraft file", f"`{Path(files.aircraft).name}` (`{files.aircraft}`)"))
    add(_row("Flight-plan file", f"`{Path(files.flight_plans).name}` (`{files.flight_plans}`)"))
    add(_row("Generated (UTC)", generated_at.strftime("%Y-%m-%d %H:%M:%S")))
    add("")

    # 2. Validation ---------------------------------------------------------
    add("## 2. Input validation")
    add("")
    if det.validation_issues:
        add(_row("Code", "Source", "Location", "Message"))
        add(_row("---", "---", "---", "---"))
        for issue in det.validation_issues:
            add(_row(f"`{issue.code.value}`", issue.source, issue.location or "-", issue.message))
    else:
        add("All inputs passed validation.")
    add("")

    # 3. Overview -----------------------------------------------------------
    add("## 3. Airspace and aircraft overview")
    add("")
    scenario = analysis.scenario
    if scenario is None:
        add("_Not available: inputs failed validation before a scenario could be built._")
    else:
        add(f"**Waypoints ({len(scenario.waypoints)})**")
        add("")
        add(_row("ID", "Latitude", "Longitude"))
        add(_row("---", "---:", "---:"))
        for wp in scenario.waypoints:
            add(_row(wp.id, _fmt(wp.latitude), _fmt(wp.longitude)))
        add("")
        add(f"**Directed edges ({len(scenario.edges)})**")
        add("")
        add(_row("From", "To", "Distance (NM)"))
        add(_row("---", "---", "---:"))
        for edge in scenario.edges:
            add(_row(edge.source, edge.target, _fmt(edge.distance_nm)))
        add("")
        add(f"**Aircraft and flight plans ({len(scenario.flight_plans)} plans)**")
        add("")
        speeds = {a.id: a.speed_kt for a in scenario.aircraft}
        add(_row("Aircraft", "Speed (kt)", "Route", "Departure (s)", "Cruise altitude (ft)"))
        add(_row("---", "---:", "---", "---:", "---:"))
        for plan in scenario.flight_plans:
            add(
                _row(
                    plan.aircraft_id,
                    _fmt(speeds.get(plan.aircraft_id, float("nan"))),
                    " → ".join(plan.route),
                    _fmt(plan.departure_time_s),
                    _fmt(plan.cruise_altitude_ft),
                )
            )
    add("")

    # 4. Thresholds & assumptions ------------------------------------------
    minima = det.separation_minima
    add("## 4. Separation thresholds and model assumptions")
    add("")
    add(f"- Horizontal (lateral) separation minimum: **{_fmt(minima.lateral_threshold_nm)} NM**")
    add(f"- Vertical separation minimum: **{_fmt(minima.vertical_threshold_ft)} ft**")
    add("- A conflict requires *both* minima to be infringed at the same closest-approach time.")
    add("")
    for item in ASSUMPTIONS:
        add(f"- {item}")
    add("")

    # 5. Conflicts ----------------------------------------------------------
    add("## 5. Detected conflicts")
    add("")
    if det.conflicts:
        add(_row("#", "Aircraft", "Time (s)", "Horizontal (NM)", "Vertical (ft)", "Segment 1", "Segment 2"))
        add(_row("---", "---", "---:", "---:", "---:", "---", "---"))
        for i, c in enumerate(det.conflicts, start=1):
            add(
                _row(
                    i,
                    f"{c.aircraft_1} vs {c.aircraft_2}",
                    _fmt(c.time_s),
                    _fmt(c.horizontal_distance_nm),
                    _fmt(c.vertical_distance_ft),
                    " → ".join(c.segment_1),
                    " → ".join(c.segment_2),
                )
            )
    elif det.is_valid:
        add("No conflicts detected.")
    else:
        add("_No conflicts listed, but the analysis is **incomplete** because of input validation failures._")
    add("")

    # 6. Resolutions --------------------------------------------------------
    add("## 6. Proposed resolutions")
    add("")
    if analysis.resolutions:
        add(_row("Conflict", "Status", "Summary", "Validation notes"))
        add(_row("---", "---", "---", "---"))
        for r in analysis.resolutions:
            conflict_no = next((n for n, c in enumerate(det.conflicts, start=1) if c == r.conflict), "?")
            add(_row(conflict_no, f"`{r.status.value}`", r.summary, "; ".join(r.validation_notes) or "-"))
        if all(r.status is ResolutionStatus.NOT_IMPLEMENTED for r in analysis.resolutions):
            add("")
            add("Tactical maneuver planning is **NOT_IMPLEMENTED**; all conflicts remain **UNRESOLVED**.")
    elif det.has_conflicts:
        add("No resolution proposals were produced; all conflicts remain **UNRESOLVED**.")
    else:
        add("Not applicable (no conflicts to resolve).")
    add("")

    # Optional LLM narrative ------------------------------------------------
    if llm_summary:
        add("## Appendix: LLM-generated narrative (non-authoritative)")
        add("")
        add("> The text below was produced by an LLM agent. Figures and statuses above are authoritative.")
        add("")
        add(llm_summary.strip())
        add("")

    # 7. Final status -------------------------------------------------------
    add("## 7. Final analysis status and limitations")
    add("")
    add(f"**Status: `{status.value}`**")
    add("")
    add(STATUS_EXPLANATIONS[status])
    add("")
    add("**Clearance status:** No clearance is issued. This is a simulation result.")
    add("")
    for item in LIMITATIONS:
        add(f"- {item}")
    add("")
    return "\n".join(out)
