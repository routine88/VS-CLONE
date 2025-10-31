"""Tests for the Tkinter MVP viewer helpers."""

from __future__ import annotations

import pytest
from _pytest.logging import LogCaptureFixture
from pathlib import Path

from game.mvp import MvpConfig, MvpReport
from game.mvp_graphics import MvpVisualizer
from game.mvp_viewer import CanvasTranslator, MvpViewerApp


def _short_config() -> MvpConfig:
    return MvpConfig(duration=20.0, tick_rate=0.5, spawn_interval_start=3.0, spawn_interval_end=1.0)


def _sample_report() -> MvpReport:
    return MvpReport(
        seed=42,
        survived=True,
        duration=120.0,
        enemies_defeated=15,
        enemy_type_counts={"swarm": 10, "bruiser": 5},
        level_reached=3,
        soul_shards=120,
        upgrades_applied=["Damage", "Fire Rate"],
        dash_count=7,
        events=[],
        final_health=54.0,
    )


def test_canvas_translator_creates_drawables() -> None:
    visualizer = MvpVisualizer()
    result = visualizer.run(seed=2, config=_short_config())

    translator = CanvasTranslator()
    first_frame = result.frames[0]
    drawables = translator.translate(first_frame)

    assert any(d.kind == "background" for d in drawables)
    assert any(d.kind == "player" for d in drawables)


def test_canvas_translator_uses_custom_palette() -> None:
    visualizer = MvpVisualizer()
    result = visualizer.run(seed=4, config=_short_config())

    translator = CanvasTranslator(palette={"player": "#123456"})
    drawables = translator.translate(result.frames[0])
    player = next(d for d in drawables if d.kind == "player")

    assert player.color == "#123456"


def test_write_report_log_handles_permission_error(
    tmp_path: Path, caplog: LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = MvpViewerApp()
    log_file = tmp_path / "logs" / "mvp.log"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("existing\n", encoding="utf-8")

    def _raise_permission_error(self: Path, *args: object, **kwargs: object):  # type: ignore[override]
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "open", _raise_permission_error)

    with caplog.at_level("WARNING"):
        app._write_report_log(_sample_report(), log_file)

    assert "Could not write viewer log" in caplog.text
