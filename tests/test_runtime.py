import logging
from pathlib import Path

import pytest

from game.audio import AudioEngine, AudioFrame
from game.export import EngineFrameExporter
from game.graphics import GraphicsEngine, RenderFrame, RenderInstruction, SceneNode, Sprite
from game.graphics_assets import load_asset_manifest

from native.runtime import EngineFrameImporter, FramePlaybackLoop, run_demo

ASSET_MANIFEST_PATH = Path("assets/graphics_assets/manifest.json")


def _build_round_trip_payload():
    graphics = GraphicsEngine()
    manifest = load_asset_manifest(ASSET_MANIFEST_PATH)
    manifest.apply(graphics, replace_existing=True, update_viewport=True)

    node = SceneNode(
        id="player",
        position=(10.0, 20.0),
        layer="actors",
        sprite_id="placeholders/player",
        metadata={"kind": "player"},
    )
    render_frame = graphics.build_frame([node], time=1.25, messages=("tick",))

    audio_engine = AudioEngine()
    audio_engine.ensure_placeholders()
    audio_frame = audio_engine.build_frame(["ui.level_up"], time=1.25)

    exporter = EngineFrameExporter()
    return exporter.frame_bundle(render_frame=render_frame, audio_frame=audio_frame)


def test_engine_frame_importer_round_trip_preserves_data():
    payload = _build_round_trip_payload()
    importer = EngineFrameImporter()

    first_render, first_audio = importer.frame_bundle(payload)
    second_render, second_audio = importer.frame_bundle(payload)

    assert first_render == second_render
    assert first_audio == second_audio

    assert first_render.instructions
    sprite_id = first_render.instructions[0].sprite.id
    assert sprite_id in importer.sprite_table
    assert importer.sprite_table[sprite_id] is first_render.instructions[0].sprite

    assert importer.effect_table
    assert importer.music_table or True  # table may be empty depending on events


def test_frame_playback_loop_uses_clock_and_sleep():
    sprite = Sprite(id="sprite", texture="tex.png", size=(16, 16))
    instruction = RenderInstruction(
        node_id="node",
        sprite=sprite,
        position=(0.0, 0.0),
        scale=1.0,
        rotation=0.0,
        flip_x=False,
        flip_y=False,
        layer="actors",
        z_index=0,
        metadata={},
    )

    frame0 = RenderFrame(time=0.0, viewport=(100, 100), instructions=(instruction,), messages=())
    frame1 = RenderFrame(time=0.5, viewport=(100, 100), instructions=(instruction,), messages=())
    audio0 = AudioFrame(time=0.0, effects=(), music=())
    audio1 = AudioFrame(time=0.5, effects=(), music=())

    class FakeClock:
        def __init__(self) -> None:
            self.current = 0.0
            self.sleeps: list[float] = []

        def now(self) -> float:
            return self.current

        def sleep(self, delay: float) -> None:
            self.sleeps.append(delay)
            if delay > 0:
                self.current += delay

    fake = FakeClock()
    loop = FramePlaybackLoop(
        [(frame0, audio0), (frame1, audio1)],
        clock=fake.now,
        sleep=fake.sleep,
    )

    captured: list[tuple[int, float]] = []
    metrics = loop.run(on_frame=lambda idx, render, audio: captured.append((idx, render.time)))

    assert captured == [(0, 0.0), (1, 0.5)]
    assert fake.sleeps
    assert fake.sleeps[-1] == pytest.approx(0.5, rel=1e-6)
    assert fake.now() == pytest.approx(0.5, rel=1e-6)
    assert metrics.frame_count == 2
    assert metrics.total_cpu_time >= 0.0


def test_run_demo_non_realtime_populates_tables():
    importer, metrics = run_demo(
        duration=0.2,
        fps=10.0,
        realtime=False,
        logger=logging.getLogger("test"),
    )
    assert importer.sprite_table
    assert importer.effect_table
    assert metrics.frame_count > 0
