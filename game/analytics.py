"""Analytics helpers for Nightfall Survivors prototype telemetry."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable, List, Mapping, MutableMapping, Optional, Sequence

from .game_state import GameEvent
from .prototype import PrototypeTranscript
from .session import RunResult


_UPGRADE_GLYPH_RE = re.compile(r"^Glyph added: (?P<family>[a-z]+)")
_UPGRADE_WEAPON_RE = re.compile(r"^Weapon upgraded: (?P<name>.+) tier (?P<tier>\d+)")
_UPGRADE_PERK_RE = re.compile(r"^Survival perk acquired: (?P<name>.+)")
_GLYPH_SET_RE = re.compile(r"^Ultimate unlocked for (?P<family>[a-z]+)!$")
_PHASE_RE = re.compile(r"^Phase advanced to (?P<phase>\d+)\.")
_HAZARD_RE = re.compile(r"^Hazard triggered:")
_BARRICADE_RE = re.compile(r"yielded (?P<amount>\d+) salvage\.")
_RESOURCE_RE = re.compile(r"Collected .+ for (?P<amount>\d+) salvage\.")
_WEATHER_RE = re.compile(r"^Weather shift:")
_ENV_DEATH_RE = re.compile(r"overwhelmed by the environment|succumbs to the onslaught")
_FINAL_BOSS_RE = re.compile(r"final[ _]boss", re.IGNORECASE)


@dataclass
class RunMetrics:
    """Normalized metrics extracted from a single run."""

    survived: bool
    duration: float
    encounters_resolved: int
    relics_collected: int
    sigils_earned: int
    total_upgrades: int
    unique_upgrades: int
    glyph_sets_completed: int
    max_phase_reached: int
    hazard_triggers: int
    weather_events: int
    salvage_collected: int
    environment_death: bool
    faced_final_boss: bool
    hunter_id: Optional[str] = None

    @property
    def upgrade_diversity(self) -> float:
        """Return the ratio of unique upgrade cards selected."""

        if self.total_upgrades == 0:
            return 0.0
        return self.unique_upgrades / self.total_upgrades


@dataclass
class AggregateMetrics:
    """Aggregated telemetry suitable for KPI tracking."""

    total_runs: int
    survival_rate: float
    average_duration: float
    median_duration: float
    average_encounters: float
    average_sigils: float
    average_upgrade_diversity: float
    environment_death_rate: float
    final_boss_rate: float
    average_salvage: float
    phase_distribution: Mapping[int, float]


def derive_metrics(result: RunResult, *, hunter_id: Optional[str] = None) -> RunMetrics:
    """Convert a :class:`RunResult` into structured metrics."""

    total_upgrades = 0
    unique_upgrades: set[str] = set()
    glyph_sets = 0
    max_phase = 1
    hazard_triggers = 0
    weather_events = 0
    salvage = 0
    environment_death = False
    faced_final_boss = bool(result.final_summary and result.final_summary.kind == "final_boss")

    for event in result.events:
        message = event.message
        match = _UPGRADE_GLYPH_RE.match(message)
        if match:
            family = match.group("family")
            total_upgrades += 1
            unique_upgrades.add(f"glyph:{family}")
            continue

        match = _UPGRADE_WEAPON_RE.match(message)
        if match:
            total_upgrades += 1
            unique_upgrades.add(f"weapon:{match.group('name')}:{match.group('tier')}")
            continue

        match = _UPGRADE_PERK_RE.match(message)
        if match:
            total_upgrades += 1
            unique_upgrades.add(f"perk:{match.group('name')}")
            continue

        match = _GLYPH_SET_RE.match(message)
        if match:
            glyph_sets += 1
            continue

        match = _PHASE_RE.match(message)
        if match:
            max_phase = max(max_phase, int(match.group("phase")))
            continue

        if _HAZARD_RE.match(message):
            hazard_triggers += 1
            continue

        if _WEATHER_RE.match(message):
            weather_events += 1
            continue

        match = _BARRICADE_RE.search(message) or _RESOURCE_RE.search(message)
        if match:
            salvage += int(match.group("amount"))
            continue

        if _ENV_DEATH_RE.search(message):
            environment_death = True

        if not faced_final_boss and _FINAL_BOSS_RE.search(message):
            faced_final_boss = True

    return RunMetrics(
        survived=result.survived,
        duration=result.duration,
        encounters_resolved=result.encounters_resolved,
        relics_collected=len(result.relics_collected),
        sigils_earned=result.sigils_earned,
        total_upgrades=total_upgrades,
        unique_upgrades=len(unique_upgrades),
        glyph_sets_completed=glyph_sets,
        max_phase_reached=max_phase,
        hazard_triggers=hazard_triggers,
        weather_events=weather_events,
        salvage_collected=salvage,
        environment_death=environment_death,
        faced_final_boss=faced_final_boss,
        hunter_id=hunter_id,
    )


def aggregate_metrics(metrics: Sequence[RunMetrics]) -> AggregateMetrics:
    """Aggregate a sequence of :class:`RunMetrics` into KPI-style data."""

    if not metrics:
        raise ValueError("metrics sequence cannot be empty")

    totals = len(metrics)
    survival_rate = sum(1 for metric in metrics if metric.survived) / totals
    average_duration = mean(metric.duration for metric in metrics)
    median_duration = median(metric.duration for metric in metrics)
    average_encounters = mean(metric.encounters_resolved for metric in metrics)
    average_sigils = mean(metric.sigils_earned for metric in metrics)
    average_diversity = mean(metric.upgrade_diversity for metric in metrics)
    environment_death_rate = sum(1 for metric in metrics if metric.environment_death) / totals
    final_boss_rate = sum(1 for metric in metrics if metric.faced_final_boss) / totals
    average_salvage = mean(metric.salvage_collected for metric in metrics)

    phase_counts: MutableMapping[int, int] = Counter()
    for metric in metrics:
        phase_counts[metric.max_phase_reached] += 1

    phase_distribution = {phase: count / totals for phase, count in sorted(phase_counts.items())}

    return AggregateMetrics(
        total_runs=totals,
        survival_rate=survival_rate,
        average_duration=average_duration,
        median_duration=median_duration,
        average_encounters=average_encounters,
        average_sigils=average_sigils,
        average_upgrade_diversity=average_diversity,
        environment_death_rate=environment_death_rate,
        final_boss_rate=final_boss_rate,
        average_salvage=average_salvage,
        phase_distribution=phase_distribution,
    )


def kpi_snapshot(metrics: Sequence[RunMetrics]) -> Mapping[str, float]:
    """Return a mapping aligned with PRD KPIs for dashboards."""

    summary = aggregate_metrics(metrics)
    return {
        "runs": float(summary.total_runs),
        "survival_rate": summary.survival_rate,
        "average_run_duration": summary.average_duration,
        "median_run_duration": summary.median_duration,
        "average_upgrade_diversity": summary.average_upgrade_diversity,
        "environment_death_rate": summary.environment_death_rate,
        "final_boss_rate": summary.final_boss_rate,
        "average_sigils": summary.average_sigils,
        "average_salvage": summary.average_salvage,
    }


def from_transcripts(transcripts: Iterable[PrototypeTranscript]) -> List[RunMetrics]:
    """Derive metrics from prototype transcripts."""

    derived: List[RunMetrics] = []
    for transcript in transcripts:
        derived.append(derive_metrics(transcript.run_result, hunter_id=transcript.hunter_id))
    return derived


def render_report(metrics: Sequence[RunMetrics]) -> str:
    """Render a formatted analytics report for console dashboards."""

    summary = aggregate_metrics(metrics)
    lines = [
        "Nightfall Survivors Analytics Report",
        f"Total Runs: {summary.total_runs}",
        f"Survival Rate: {summary.survival_rate:.2%}",
        f"Average Duration: {summary.average_duration:.1f}s (median {summary.median_duration:.1f}s)",
        f"Average Encounters: {summary.average_encounters:.1f}",
        f"Average Upgrade Diversity: {summary.average_upgrade_diversity:.2f}",
        f"Final Boss Rate: {summary.final_boss_rate:.2%}",
        f"Environment Death Rate: {summary.environment_death_rate:.2%}",
        f"Average Sigils: {summary.average_sigils:.1f}",
        f"Average Salvage: {summary.average_salvage:.1f}",
        "Phase Distribution:",
    ]
    for phase, share in summary.phase_distribution.items():
        lines.append(f"  Phase {phase}: {share:.2%}")
    return "\n".join(lines)


def _load_transcript(path: str) -> PrototypeTranscript:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    run_payload = payload.get("run_result", {})
    events_payload = run_payload.get("events", payload.get("events", []))
    events: List[GameEvent] = []
    for entry in events_payload:
        if isinstance(entry, str):
            events.append(GameEvent(entry))
        elif isinstance(entry, Mapping):
            events.append(GameEvent(entry.get("message", "")))
        else:
            raise TypeError(f"Unsupported event payload: {entry!r}")

    result = RunResult(
        survived=run_payload.get("survived", payload.get("survived", False)),
        duration=float(run_payload.get("duration", payload.get("duration", 0.0))),
        encounters_resolved=int(run_payload.get("encounters_resolved", payload.get("encounters_resolved", 0))),
        relics_collected=list(run_payload.get("relics_collected", payload.get("relics_collected", []))),
        events=events,
        final_summary=None,
        sigils_earned=int(run_payload.get("sigils_earned", payload.get("sigils_earned", 0))),
    )

    return PrototypeTranscript(
        seed=int(payload.get("seed", 0)),
        hunter_id=payload.get("hunter_id"),
        hunter_name=payload.get("hunter_name", ""),
        survived=result.survived,
        duration=result.duration,
        encounters_resolved=result.encounters_resolved,
        relics_collected=result.relics_collected,
        sigils_earned=result.sigils_earned,
        events=[event.message for event in events],
        run_result=result,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point to generate analytics reports from transcripts."""

    parser = argparse.ArgumentParser(description="Nightfall Survivors analytics generator")
    parser.add_argument("transcript", nargs="+", help="Path to transcript JSON files produced by the prototype.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary instead of text output.")

    args = parser.parse_args(argv)

    transcripts = [_load_transcript(path) for path in args.transcript]

    metrics = from_transcripts(transcripts)
    if args.json:
        print(json.dumps(kpi_snapshot(metrics), indent=2))
    else:
        print(render_report(metrics))
    return 0


__all__ = [
    "AggregateMetrics",
    "RunMetrics",
    "aggregate_metrics",
    "derive_metrics",
    "from_transcripts",
    "kpi_snapshot",
    "render_report",
]


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    raise SystemExit(main())
