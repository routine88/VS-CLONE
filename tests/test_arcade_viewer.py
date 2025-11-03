"""Tests for the arcade graphical viewer bridge."""

from __future__ import annotations

from game.arcade_viewer import ArcadeViewerApp, ArcadeVisualizer


def test_arcade_visualizer_generates_frames() -> None:
    visualizer = ArcadeVisualizer(duration=15.0, tick_step=0.2)
    result = visualizer.run(seed=3)

    assert result.frames, "expected at least one render frame"
    assert len(result.frames) == len(result.audio_frames)
    assert len(result.frames) == len(result.snapshots)

    first_frame = result.frames[0]
    assert any(instr.metadata.get("kind") == "player" for instr in first_frame.instructions)


def test_arcade_viewer_summary_highlights_outcome() -> None:
    visualizer = ArcadeVisualizer(duration=10.0, tick_step=0.25)
    result = visualizer.run(seed=5)

    app = ArcadeViewerApp(visualizer=visualizer)
    summary = app._format_summary(result)

    assert "Arcade Prototype Run" in summary
    assert "Duration" in summary
    assert "Health" in summary
