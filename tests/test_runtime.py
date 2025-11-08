import logging
from pathlib import Path

import json
import logging
from pathlib import Path

import pytest

from game.audio import AudioEngine
from game.export import EngineFrameExporter
from game.graphics import GraphicsEngine, SceneNode
from game.graphics_assets import load_asset_manifest

from native.runtime import (
    AudioRegistry,
    FramePlaybackLoop,
    RendererProject,
    SpriteRegistry,
    build_placeholder_scene,
    iter_jsonl_lines,
)

ASSET_MANIFEST_PATH = Path("assets/graphics_assets/manifest.json")
AUDIO_MANIFEST_PATH = Path("assets/audio/manifest.json")


def test_sprite_registry_reuses_manifest_handles():
    registry = SpriteRegistry(manifest_path=ASSET_MANIFEST_PATH)
    assert registry.manifest.sprites
    sprite = next(iter(registry.manifest.sprites.values()))
    descriptor = sprite.to_sprite_descriptor()

    handle_a = registry.resolve(descriptor)
    handle_b = registry.resolve(descriptor)

    assert handle_a is handle_b
    assert handle_a.manifest is sprite
    assert handle_a.texture_path.name


def test_audio_registry_resolves_manifest_assets():
    registry = AudioRegistry(manifest_path=AUDIO_MANIFEST_PATH)
    assert registry.manifest.effects
    effect_descriptor = next(iter(registry.manifest.effects.values()))

    handle = registry.resolve_effect(effect_descriptor)
    assert handle.descriptor is effect_descriptor
    assert handle.id == effect_descriptor.id

    music_descriptor = next(iter(registry.manifest.music.values()))
    music_handle = registry.resolve_music(music_descriptor)
    assert music_handle.descriptor is music_descriptor
    assert music_handle.path.name


def test_jsonl_stream_round_trip():
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

    render_frame = graphics.build_frame([node], time=0.25, messages=("tick",))
    audio_engine = AudioEngine()
    audio_engine.ensure_placeholders()
    audio_frame = audio_engine.build_frame(["ui.level_up"], time=0.25)

    exporter = EngineFrameExporter()
    payload = exporter.frame_bundle(render_frame=render_frame, audio_frame=audio_frame)
    json_line = json.dumps(payload)

    bundles = tuple(iter_jsonl_lines([json_line]))
    assert len(bundles) == 1
    parsed_render, parsed_audio = bundles[0]
    assert parsed_render.time == pytest.approx(render_frame.time)
    assert parsed_render.viewport == render_frame.viewport
    assert parsed_audio is not None
    assert parsed_audio.time == pytest.approx(audio_frame.time)


def test_frame_playback_loop_applies_frames_and_overrides():
    graphics = GraphicsEngine()
    manifest = load_asset_manifest(ASSET_MANIFEST_PATH)
    manifest.apply(graphics, replace_existing=True, update_viewport=True)

    audio_engine = AudioEngine()
    audio_engine.ensure_placeholders()

    exporter = EngineFrameExporter()
    bundles = build_placeholder_scene(
        graphics,
        duration=0.3,
        fps=10.0,
        audio=audio_engine,
        exporter=exporter,
    )

    sprite_registry = SpriteRegistry(manifest_path=ASSET_MANIFEST_PATH)
    audio_registry = AudioRegistry(manifest_path=AUDIO_MANIFEST_PATH)
    project = RendererProject(sprite_registry=sprite_registry, audio_registry=audio_registry)

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
    loop = FramePlaybackLoop(bundles, clock=fake.now, sleep=fake.sleep)

    captured: list[tuple[int, float]] = []
    metrics = loop.run(on_frame=lambda idx, render, audio: captured.append((idx, render.time)))

    assert captured == [(0, 0.0), (1, 0.5)]
    assert fake.sleeps
    assert fake.sleeps[-1] == pytest.approx(0.5, rel=1e-6)
    assert fake.now() == pytest.approx(0.5, rel=1e-6)
    assert metrics.frame_count == 2
    assert metrics.total_cpu_time >= 0.0

    loop.run(
        project,
        input_override=override_callback,
        on_applied=lambda idx, applied: applied_frames.append(applied),
    )

    assert applied_frames
    assert project.telemetry.render_frames == len(applied_frames)
    assert project.telemetry.audio_frames == len([frame for frame in applied_frames if frame.audio.frame])
    assert project.telemetry.missing_sprites == 0
    assert project.telemetry.missing_effects == 0
    assert project.telemetry.missing_music == 0
    assert project.telemetry.overrides_applied == len(applied_frames) - 1

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
