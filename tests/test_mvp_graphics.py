"""Integration checks for MVP graphics bridge."""

from __future__ import annotations

from game.graphics import GraphicsEngine
from game.mvp import MvpConfig, run_mvp_simulation, run_mvp_with_snapshots
from game.mvp_graphics import MvpVisualizer


def test_mvp_visualizer_matches_simulation_report() -> None:
    config = MvpConfig(duration=60.0, tick_rate=0.5, spawn_interval_start=3.5, spawn_interval_end=1.2)
    graphics = GraphicsEngine(viewport=(640, 360))
    visualizer = MvpVisualizer(graphics=graphics)

    result = visualizer.run(seed=5, config=config)
    reference_report = run_mvp_simulation(seed=5, config=config)

    assert result.report == reference_report
    assert result.frames, "expected at least one render frame"
    assert result.audio_frames, "expected audio frames to accompany render output"
    assert len(result.frames) == len(result.audio_frames)

    first_frame = result.frames[0]
    assert any(instr.metadata.get("kind") == "player" for instr in first_frame.instructions)
    assert any("Health:" in message for message in first_frame.messages)

    assert any(
        any(instr.metadata.get("kind") == "enemy" for instr in frame.instructions)
        for frame in result.frames
    ), "expected an enemy to appear in at least one frame"

    assert any(frame.effects for frame in result.audio_frames), "audio cues should be emitted"


def test_mvp_visualizer_tracks_snapshots() -> None:
    config = MvpConfig(duration=45.0, tick_rate=0.5, spawn_interval_start=3.0, spawn_interval_end=1.0)
    report, snapshots = run_mvp_with_snapshots(seed=11, config=config)

    visualizer = MvpVisualizer()
    result = visualizer.run(seed=11, config=config)

    assert result.report == report
    assert len(result.frames) == len(snapshots)
    assert len(result.audio_frames) == len(result.frames)
    assert all(frame.messages for frame in result.frames[:3])
