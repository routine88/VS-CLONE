"""Tests for the Tkinter MVP viewer helpers."""

from __future__ import annotations

from game.mvp import MvpConfig
from game.mvp_graphics import MvpVisualizer
from game.mvp_viewer import CanvasTranslator


def _short_config() -> MvpConfig:
    return MvpConfig(duration=20.0, tick_rate=0.5, spawn_interval_start=3.0, spawn_interval_end=1.0)


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
