"""Shared run metric derivation helpers for Nightfall Survivors."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable, List, Mapping, MutableMapping, Optional, Sequence

from .game_state import GameEvent
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
    average_relics: float
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
        raise ValueError("At least one metrics entry is required")

    total_runs = len(metrics)
    survival_rate = sum(1 for metric in metrics if metric.survived) / total_runs
    average_duration = mean(metric.duration for metric in metrics)
    median_duration = median(metric.duration for metric in metrics)
    average_encounters = mean(metric.encounters_resolved for metric in metrics)
    average_sigils = mean(metric.sigils_earned for metric in metrics)
    average_relics = mean(metric.relics_collected for metric in metrics)
    average_upgrade_diversity = mean(metric.upgrade_diversity for metric in metrics)
    environment_death_rate = sum(1 for metric in metrics if metric.environment_death) / total_runs
    final_boss_rate = sum(1 for metric in metrics if metric.faced_final_boss) / total_runs
    average_salvage = mean(metric.salvage_collected for metric in metrics)

    phase_counter: MutableMapping[int, int] = Counter()
    for metric in metrics:
        phase_counter[metric.max_phase_reached] += 1
    phase_distribution = {phase: count / total_runs for phase, count in sorted(phase_counter.items())}

    return AggregateMetrics(
        total_runs=total_runs,
        survival_rate=survival_rate,
        average_duration=average_duration,
        median_duration=median_duration,
        average_encounters=average_encounters,
        average_sigils=average_sigils,
        average_relics=average_relics,
        average_upgrade_diversity=average_upgrade_diversity,
        environment_death_rate=environment_death_rate,
        final_boss_rate=final_boss_rate,
        average_salvage=average_salvage,
        phase_distribution=phase_distribution,
    )


def kpi_snapshot(metrics: Sequence[RunMetrics]) -> Mapping[str, float]:
    """Return a JSON-friendly KPI snapshot."""

    summary = aggregate_metrics(metrics)
    return {
        "total_runs": float(summary.total_runs),
        "survival_rate": summary.survival_rate,
        "average_run_duration": summary.average_duration,
        "median_run_duration": summary.median_duration,
        "average_upgrade_diversity": summary.average_upgrade_diversity,
        "environment_death_rate": summary.environment_death_rate,
        "final_boss_rate": summary.final_boss_rate,
        "average_sigils": summary.average_sigils,
        "average_relics": summary.average_relics,
        "average_salvage": summary.average_salvage,
    }


def format_run_summary(metrics: RunMetrics) -> str:
    """Create a human-readable summary of derived metrics."""

    outcome = "Survived" if metrics.survived else "Fallen"
    diversity = metrics.upgrade_diversity
    diversity_percent = f"{diversity:.0%}" if diversity else "0%"

    lines = [
        "Analytics Summary:",
        f"  Outcome: {outcome}",
        f"  Duration: {metrics.duration:.1f}s",
        f"  Encounters Resolved: {metrics.encounters_resolved}",
        f"  Max Phase Reached: {metrics.max_phase_reached}",
        f"  Glyph Sets Completed: {metrics.glyph_sets_completed}",
        f"  Upgrades Taken: {metrics.total_upgrades} ({diversity_percent} unique)",
        f"  Relics Collected: {metrics.relics_collected}",
        f"  Hazard Triggers: {metrics.hazard_triggers}",
        f"  Weather Events: {metrics.weather_events}",
        f"  Salvage Collected: {metrics.salvage_collected}",
        f"  Sigils Earned: {metrics.sigils_earned}",
        f"  Faced Final Boss: {'Yes' if metrics.faced_final_boss else 'No'}",
    ]

    if not metrics.survived:
        cause = "Environment Overrun" if metrics.environment_death else "Horde Overrun"
        lines.append(f"  Defeat Cause: {cause}")

    if metrics.hunter_id:
        lines.append(f"  Hunter: {metrics.hunter_id}")

    return "\n".join(lines)


__all__ = [
    "AggregateMetrics",
    "RunMetrics",
    "aggregate_metrics",
    "derive_metrics",
    "format_run_summary",
    "kpi_snapshot",
]

