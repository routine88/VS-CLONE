"""Tests for KPI aggregation utilities."""

from __future__ import annotations

import pytest

from game.metrics import RunMetrics, aggregate_by_hunter, hunter_kpis


def make_run_metrics(
    *,
    hunter_id: str | None,
    survived: bool,
    duration: float,
    encounters: int = 8,
    relics: int = 2,
    sigils: int = 10,
    upgrades: int = 5,
    unique_upgrades: int = 3,
    glyph_sets: int = 1,
    max_phase: int = 3,
    hazard_triggers: int = 1,
    weather_events: int = 0,
    salvage: int = 25,
) -> RunMetrics:
    return RunMetrics(
        survived=survived,
        duration=duration,
        encounters_resolved=encounters,
        relics_collected=relics,
        sigils_earned=sigils,
        total_upgrades=upgrades,
        unique_upgrades=unique_upgrades,
        glyph_sets_completed=glyph_sets,
        max_phase_reached=max_phase,
        hazard_triggers=hazard_triggers,
        weather_events=weather_events,
        salvage_collected=salvage,
        environment_death=not survived,
        faced_final_boss=True,
        hunter_id=hunter_id,
    )


def test_aggregate_by_hunter_groups_and_summarises() -> None:
    metrics = [
        make_run_metrics(hunter_id="hunter_varik", survived=True, duration=120.0),
        make_run_metrics(hunter_id="hunter_varik", survived=False, duration=60.0),
        make_run_metrics(hunter_id="hunter_mira", survived=True, duration=90.0, sigils=14),
    ]

    breakdown = aggregate_by_hunter(metrics)

    assert set(breakdown) == {"hunter_varik", "hunter_mira"}

    varik_summary = breakdown["hunter_varik"]
    assert varik_summary.total_runs == 2
    assert varik_summary.survival_rate == pytest.approx(0.5)
    assert varik_summary.average_duration == pytest.approx(90.0)

    mira_summary = breakdown["hunter_mira"]
    assert mira_summary.total_runs == 1
    assert mira_summary.average_sigils == pytest.approx(14.0)


def test_aggregate_by_hunter_includes_unidentified_when_requested() -> None:
    metrics = [
        make_run_metrics(hunter_id=None, survived=True, duration=75.0),
    ]

    breakdown = aggregate_by_hunter(metrics, include_unidentified=True, unidentified_key="anon")

    assert set(breakdown) == {"anon"}
    assert breakdown["anon"].total_runs == 1


def test_hunter_kpis_returns_snapshot() -> None:
    metrics = [
        make_run_metrics(hunter_id="hunter_mira", survived=True, duration=100.0, sigils=12),
        make_run_metrics(hunter_id="hunter_mira", survived=True, duration=80.0, sigils=18),
    ]

    snapshot = hunter_kpis(metrics)

    assert set(snapshot) == {"hunter_mira"}
    data = snapshot["hunter_mira"]
    assert data["total_runs"] == pytest.approx(2.0)
    assert data["survival_rate"] == pytest.approx(1.0)
    assert data["average_sigils"] == pytest.approx(15.0)
