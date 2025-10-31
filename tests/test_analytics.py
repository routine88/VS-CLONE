"""Tests covering analytics instrumentation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game import analytics
from game.game_state import GameEvent
from game.prototype import PrototypeSession, transcript_to_dict
from game.session import RunResult


def make_run_result(**overrides):
    events = [
        GameEvent("Phase advanced to 2."),
        GameEvent("Glyph added: blood"),
        GameEvent("Weapon upgraded: Dusk Repeater tier 2"),
        GameEvent("Survival perk acquired: Reinforced Plating"),
        GameEvent("Ultimate unlocked for blood!"),
        GameEvent("Hazard triggered: Grave Spikes in the graveyard (-8 HP)."),
        GameEvent("Barricade cleared: Rotten Fence yielded 12 salvage."),
        GameEvent("Collected Moon Cache for 7 salvage."),
        GameEvent("Weather shift: Blood Rain (sapping winds) movement -20% vision -10%"),
        GameEvent("The final boss Dawn Revenant descends for the last stand."),
    ]

    base = dict(
        survived=True,
        duration=600.0,
        encounters_resolved=9,
        relics_collected=["Moonlit Charm"],
        events=events,
        final_summary=None,
        sigils_earned=28,
    )
    base.update(overrides)
    return RunResult(**base)


def test_derive_metrics_extracts_expected_values() -> None:
    result = make_run_result()
    metrics = analytics.derive_metrics(result, hunter_id="hunter_varik")

    assert metrics.survived is True
    assert metrics.total_upgrades == 3
    assert metrics.unique_upgrades == 3
    assert metrics.glyph_sets_completed == 1
    assert metrics.max_phase_reached == 2
    assert metrics.hazard_triggers == 1
    assert metrics.weather_events == 1
    assert metrics.salvage_collected == 19
    assert metrics.environment_death is False
    assert metrics.faced_final_boss is True
    assert metrics.upgrade_diversity == pytest.approx(1.0)
    assert metrics.hunter_id == "hunter_varik"


def test_aggregate_metrics_computes_kpis() -> None:
    metric_a = analytics.derive_metrics(make_run_result(duration=720.0))
    metric_b = analytics.derive_metrics(
        make_run_result(
            survived=False,
            duration=480.0,
            encounters_resolved=6,
            events=[
                GameEvent("Phase advanced to 3."),
                GameEvent("Glyph added: storm"),
                GameEvent("Glyph added: storm"),
                GameEvent("Hazard triggered: Blood Geyser in the forest (-12 HP)."),
                GameEvent("The hunter is overwhelmed by the environment."),
            ],
            sigils_earned=15,
        )
    )

    summary = analytics.aggregate_metrics([metric_a, metric_b])
    assert summary.total_runs == 2
    assert summary.survival_rate == pytest.approx(0.5)
    assert summary.average_duration == pytest.approx((720.0 + 480.0) / 2)
    assert summary.environment_death_rate == pytest.approx(0.5)
    assert summary.average_relics == pytest.approx(1.0)
    assert summary.phase_distribution == {2: 0.5, 3: 0.5}

    snapshot = analytics.kpi_snapshot([metric_a, metric_b])
    assert snapshot["survival_rate"] == pytest.approx(0.5)
    assert "average_upgrade_diversity" in snapshot
    assert snapshot["average_relics"] == pytest.approx(1.0)


def test_from_transcripts_and_render_report(tmp_path: Path) -> None:
    session = PrototypeSession()
    transcript = session.run(seed=1337, total_duration=120.0, tick_step=10.0)

    payload = transcript_to_dict(transcript)
    path = tmp_path / "transcript.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    metrics = analytics.from_transcripts([transcript])
    assert len(metrics) == 1

    report = analytics.render_report(metrics)
    assert "Nightfall Survivors Analytics Report" in report
    assert "Hunter Breakdown:" in report
    assert "hunter_mira" in report

    exit_code = analytics.main(["--json", str(path)])
    assert exit_code == 0
