"""Tests for the MVP-focused simulation module."""

from __future__ import annotations

import pytest

from game.mvp import (
    EnemyArchetype,
    MvpConfig,
    main,
    run_mvp_simulation,
    run_mvp_with_snapshots,
)


def test_mvp_simulation_generates_progression() -> None:
    config = MvpConfig(
        duration=120.0,
        tick_rate=0.5,
        player_damage=10.0,
        player_fire_rate=1.2,
    )
    report = run_mvp_simulation(seed=21, config=config)

    assert report.enemies_defeated > 0
    assert report.level_reached >= 2, "expected at least one level-up"
    assert report.dash_count > 0, "dash should be demonstrated in the MVP run"
    assert set(report.enemy_type_counts) == {"swarm", "bruiser"}
    assert any("Damage Boost" == upgrade for upgrade in report.upgrades_applied)
    assert report.events, "event log should not be empty"


def test_mvp_simulation_failure_condition() -> None:
    config = MvpConfig(
        duration=90.0,
        spawn_interval_start=1.8,
        spawn_interval_end=0.6,
        player_damage=6.0,
        player_max_health=35,
        player_dash_trigger=0.6,
        player_dash_distance=1.0,
        player_dash_cooldown=10.0,
        player_speed=1.2,
        bruiser_spawn_threshold=0.0,
        swarm_archetype=EnemyArchetype(
            name="Aggressive Wisp",
            health=20.0,
            speed=1.6,
            damage=14,
            xp_reward=6,
        ),
        bruiser_archetype=EnemyArchetype(
            name="Relentless Hulk",
            health=60.0,
            speed=1.2,
            damage=26,
            xp_reward=20,
        ),
    )
    report = run_mvp_simulation(seed=7, config=config)

    assert not report.survived
    assert report.final_health == 0
    assert report.enemies_defeated > 0


def test_mvp_cli_invocation(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--seed", "5", "--duration", "60", "--tick", "0.5", "--summary"])
    assert exit_code == 0

    captured = capsys.readouterr().out
    assert "Nightfall Survivors MVP Run" in captured
    assert "Event Log" in captured


def test_mvp_cli_event_limit(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["--seed", "9", "--duration", "90", "--tick", "0.5", "--summary", "--events", "5"]
    )
    assert exit_code == 0

    captured = capsys.readouterr().out
    assert "Event Log (first 5 events):" in captured
    event_lines = [line for line in captured.splitlines() if line.strip().startswith("-")]
    assert len(event_lines) <= 5
    assert event_lines, "Expected at least one event to be printed"


def test_mvp_snapshots_include_audio_events() -> None:
    config = MvpConfig(duration=45.0, tick_rate=0.5)
    _, snapshots = run_mvp_with_snapshots(seed=12, config=config)

    assert snapshots, "expected snapshots to be captured"
    assert any(snapshot.audio_events for snapshot in snapshots)
    for snapshot in snapshots:
        assert isinstance(snapshot.audio_events, tuple)

