"""CLI for executing repeatability runs of the MVP simulation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from game.mvp import MvpConfig, MvpReport, run_mvp_simulation

_DEFAULT_SEEDS: Tuple[int, ...] = (12345, 67890, 424242)


class RepeatabilityError(RuntimeError):
    """Raised when deterministic expectations are not met."""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run five-minute MVP simulations to validate repeatability and capture metrics.",
    )
    parser.add_argument(
        "--seed",
        dest="seeds",
        action="append",
        type=int,
        help="Seed to execute. Provide multiple times to cover a suite of seeds.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=2,
        help="Number of times to run each seed for determinism checks (default: 2).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=300.0,
        help="Override the simulation duration in seconds (default: 300).",
    )
    parser.add_argument(
        "--tick",
        dest="tick_rate",
        type=float,
        help="Override the simulation tick rate (seconds).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="JSON file to write metrics to. Defaults to logs/repeatability_<timestamp>.json.",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        help="Optional Markdown summary path. Defaults to matching the JSON output with .md extension.",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit with non-zero status if any seed produces non-deterministic results.",
    )
    return parser.parse_args(argv)


def _default_output_paths(provided: Path | None, provided_markdown: Path | None) -> Tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if provided is not None:
        json_path = provided.expanduser().resolve()
    else:
        json_path = Path("logs") / f"repeatability_{timestamp}.json"
    if provided_markdown is not None:
        md_path = provided_markdown.expanduser().resolve()
    else:
        md_path = json_path.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    return json_path, md_path


_MAX_EVENTS_TO_STORE = 50


def _serialise_report(report: MvpReport) -> Mapping[str, object]:
    data = asdict(report)
    # Normalise floats for readability.
    data["duration"] = round(float(data["duration"]), 3)
    data["final_health"] = round(float(data["final_health"]), 3)

    events: List[str] = list(data.get("events", []))
    digest = sha256("\n".join(events).encode("utf-8")).hexdigest() if events else ""
    data["event_count"] = len(events)
    data["event_digest"] = digest
    if len(events) > _MAX_EVENTS_TO_STORE:
        data["events"] = events[:_MAX_EVENTS_TO_STORE]
        data["events_truncated"] = len(events) - _MAX_EVENTS_TO_STORE
    return data


def _aggregate_metrics(reports: Iterable[MvpReport]) -> Mapping[str, object]:
    report_list = list(reports)
    total_runs = len(report_list)
    if total_runs == 0:
        raise ValueError("At least one report is required for aggregation")

    durations = [report.duration for report in report_list]
    enemies = [report.enemies_defeated for report in report_list]
    levels = [report.level_reached for report in report_list]
    shards = [report.soul_shards for report in report_list]
    health = [report.final_health for report in report_list]
    dash_counts = [report.dash_count for report in report_list]

    survival_rate = sum(1 for report in report_list if report.survived) / total_runs
    bruiser_counts: List[int] = [report.enemy_type_counts.get("bruiser", 0) for report in report_list]
    swarm_counts: List[int] = [report.enemy_type_counts.get("swarm", 0) for report in report_list]

    return {
        "total_runs": total_runs,
        "survival_rate": round(survival_rate, 3),
        "average_duration": round(mean(durations), 3),
        "median_duration": round(median(durations), 3),
        "average_enemies_defeated": round(mean(enemies), 3),
        "average_swarm_defeated": round(mean(swarm_counts), 3),
        "average_bruiser_defeated": round(mean(bruiser_counts), 3),
        "average_level_reached": round(mean(levels), 3),
        "average_soul_shards": round(mean(shards), 3),
        "average_final_health": round(mean(health), 3),
        "average_dash_count": round(mean(dash_counts), 3),
    }


def _compare_reports(first: Mapping[str, object], second: Mapping[str, object]) -> Mapping[str, bool]:
    keys = (
        "seed",
        "survived",
        "duration",
        "enemies_defeated",
        "enemy_type_counts",
        "level_reached",
        "soul_shards",
        "upgrades_applied",
        "event_count",
        "event_digest",
        "dash_count",
        "final_health",
    )
    return {key: first[key] == second[key] for key in keys}


def _render_markdown(
    *,
    json_path: Path,
    args: argparse.Namespace,
    determinism: Mapping[int, Mapping[str, bool]],
    summary: Mapping[str, object],
    reports: Mapping[int, Sequence[Mapping[str, object]]],
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Nightfall Survivors MVP Repeatability Check",
        "",
        f"- Generated: {timestamp}",
        f"- Output JSON: `{json_path}`",
        f"- Simulation duration: {args.duration:.1f}s",
        f"- Tick rate: {args.tick_rate if args.tick_rate is not None else MvpConfig.tick_rate:.2f}s",
        f"- Runs per seed: {args.repeat}",
        "",
        "## Determinism",
        "",
    ]
    for seed, matches in determinism.items():
        status = "PASS" if all(matches.values()) else "FAIL"
        lines.append(f"- Seed {seed}: **{status}**")
        for key, match in matches.items():
            indicator = "✅" if match else "❌"
            lines.append(f"  - {indicator} {key}")
        lines.append("")

    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    for key, value in summary.items():
        lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
    lines.append("")

    lines.append("## Per-Seed Reports")
    lines.append("")
    for seed, seed_reports in reports.items():
        lines.append(f"### Seed {seed}")
        lines.append("")
        for index, report in enumerate(seed_reports, start=1):
            lines.append(f"Run {index}:")
            lines.append("")
            lines.append("| Field | Value |")
            lines.append("| --- | --- |")
            for field, value in report.items():
                lines.append(f"| {field} | {value} |")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    seeds = tuple(args.seeds) if args.seeds else _DEFAULT_SEEDS
    if args.repeat < 1:
        raise SystemExit("--repeat must be at least 1")

    config = MvpConfig(
        duration=args.duration,
        tick_rate=args.tick_rate if args.tick_rate is not None else MvpConfig.tick_rate,
    )
    json_path, md_path = _default_output_paths(args.output, args.markdown)

    reports_by_seed: MutableMapping[int, List[MvpReport]] = {seed: [] for seed in seeds}
    serialised_reports: Dict[int, List[Mapping[str, object]]] = {seed: [] for seed in seeds}
    determinism: Dict[int, Mapping[str, bool]] = {}

    for seed in seeds:
        prior: Mapping[str, object] | None = None
        field_matches: MutableMapping[str, bool] | None = None
        for _ in range(args.repeat):
            report = run_mvp_simulation(seed=seed, config=config)
            reports_by_seed[seed].append(report)
            current = _serialise_report(report)
            serialised_reports[seed].append(current)
            if prior is None:
                prior = current
                field_matches = {key: True for key in current.keys()}
            else:
                comparisons = _compare_reports(prior, current)
                if field_matches is not None:
                    field_matches.update({key: field_matches[key] and comparisons[key] for key in comparisons})
        if field_matches is None:
            field_matches = {}
        determinism[seed] = dict(field_matches)

    all_reports: List[MvpReport] = [report for seed_reports in reports_by_seed.values() for report in seed_reports]
    summary = _aggregate_metrics(all_reports)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration": args.duration,
        "tick_rate": config.tick_rate,
        "repeat_per_seed": args.repeat,
        "seeds": list(seeds),
        "determinism": determinism,
        "summary": summary,
        "reports": serialised_reports,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown = _render_markdown(
        json_path=json_path,
        args=args,
        determinism=determinism,
        summary=summary,
        reports=serialised_reports,
    )
    md_path.write_text(markdown, encoding="utf-8")

    print(f"Repeatability data written to {json_path}")
    print(f"Markdown summary written to {md_path}")

    if args.fail_on_drift:
        for matches in determinism.values():
            if not all(matches.values()):
                raise RepeatabilityError("Non-deterministic results detected")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(run())
