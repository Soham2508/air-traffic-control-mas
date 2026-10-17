"""CLI interface for ATC Conflict Detection and Resolution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from atc_mas.config import DEFAULT_SEPARATION_MINIMA, SeparationMinima
from atc_mas.pipeline import run_analysis, write_outputs


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atc-mas",
        description="Air Traffic Control Multi-Agent System (Simulation)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser(
        "detect",
        help="Run deterministic conflict detection on scenario files",
    )
    detect_parser.add_argument(
        "--airspace",
        required=True,
        type=Path,
        help="Path to airspace GraphML file",
    )
    detect_parser.add_argument(
        "--aircraft",
        required=True,
        type=Path,
        help="Path to aircraft JSON file",
    )
    detect_parser.add_argument(
        "--flight-plans",
        required=True,
        type=Path,
        help="Path to flight plans JSON file",
    )
    detect_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output/conflict_result.json"),
        help="Output path for JSON result (default: data/output/conflict_result.json)",
    )
    detect_parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/output/atc_report.md"),
        help="Output path for Markdown report (default: data/output/atc_report.md)",
    )
    detect_parser.add_argument(
        "--lateral-threshold",
        type=float,
        default=DEFAULT_SEPARATION_MINIMA.lateral_threshold_nm,
        help=f"Horizontal separation threshold in NM (default: {DEFAULT_SEPARATION_MINIMA.lateral_threshold_nm})",
    )
    detect_parser.add_argument(
        "--vertical-threshold",
        type=float,
        default=DEFAULT_SEPARATION_MINIMA.vertical_threshold_ft,
        help=f"Vertical separation threshold in feet (default: {DEFAULT_SEPARATION_MINIMA.vertical_threshold_ft})",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "detect":
        minima = SeparationMinima(
            lateral_threshold_nm=args.lateral_threshold,
            vertical_threshold_ft=args.vertical_threshold,
        )
        analysis = run_analysis(
            airspace=args.airspace,
            aircraft=args.aircraft,
            flight_plans=args.flight_plans,
            separation_minima=minima,
        )
        write_outputs(
            analysis=analysis,
            json_path=args.output,
            report_path=args.report,
        )

        print(f"Status: {analysis.analysis_status.value}")
        print(f"Conflicts detected: {analysis.detection.conflict_count}")
        print(f"Output written to: {args.output} and {args.report}")

        if not analysis.detection.is_valid:
            print("Validation issues encountered:", file=sys.stderr)
            for issue in analysis.detection.validation_issues:
                print(f"  - {issue}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

