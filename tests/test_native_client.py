import copy
import logging
from pathlib import Path

from game.audio import AudioEngine
from game.export import EngineFrameExporter
from game.graphics import GraphicsEngine, SceneNode
from game.graphics_assets import load_asset_manifest

from native.client import (
    AudioFrameDTO,
    AudioManifestDTO,
    AudioPlaybackHarness,
    FramePlaybackHarness,
    GraphicsManifest,
    RenderFrameDTO,
)

ASSET_MANIFEST_PATH = Path("assets/graphics_assets/manifest.json")


def _build_export_payload() -> dict:
    engine = GraphicsEngine()
    manifest = load_asset_manifest(ASSET_MANIFEST_PATH)
    manifest.apply(engine, replace_existing=True, update_viewport=True)

    node = SceneNode(
        id="player",
        position=(10.0, 20.0),
        layer="actors",
        sprite_id="placeholders/player",
        metadata={"kind": "player"},
    )
    frame = engine.build_frame([node], time=2.5, messages=["tick"])
    exporter = EngineFrameExporter()
    return exporter.render_payload(frame)


def _build_audio_payload() -> dict:
    audio_engine = AudioEngine()
    frame = audio_engine.build_frame(["ui.level_up", "music.start"], time=1.25)
    exporter = EngineFrameExporter()
    return exporter.audio_payload(frame)


def test_render_frame_dto_deserialises_export():
    payload = _build_export_payload()
    dto = RenderFrameDTO.from_dict(payload)
    assert dto.time == 2.5
    assert dto.viewport == (1280, 720)
    assert dto.messages == ("tick",)
    assert len(dto.instructions) == 1
    instruction = dto.instructions[0]
    assert instruction.node_id == "player"
    assert instruction.layer == "actors"
    assert instruction.sprite.id == "placeholders/player"
    assert instruction.metadata["kind"] == "player"


def test_audio_frame_dto_deserialises_export():
    payload = _build_audio_payload()
    dto = AudioFrameDTO.from_dict(payload)
    assert dto.time == 1.25
    assert dto.effects
    assert any(instr.clip.id == "effects/ui.prompt" for instr in dto.effects)
    assert dto.music and dto.music[0].track is not None


def test_sprite_registry_resolves_manifest_entries():
    manifest = GraphicsManifest.from_path(ASSET_MANIFEST_PATH)
    harness = FramePlaybackHarness(manifest)
    sprite = harness.registry.resolve("placeholders/player")
    assert sprite is not None
    assert sprite.texture_path.exists() or sprite.texture_path.suffix == ".json"
    assert "actors" in harness.manifest.layers


def test_harness_logs_unknown_sprites_and_layers(caplog):
    payload = _build_export_payload()
    manifest = GraphicsManifest.from_path(ASSET_MANIFEST_PATH)
    harness = FramePlaybackHarness(manifest)

    caplog.set_level(logging.WARNING, logger="native.client.harness")
    result = harness.replay(payload)
    assert len(caplog.records) == 0
    assert result.instructions[0].sprite is not None
    assert result.instructions[0].layer is not None

    unknown_payload = copy.deepcopy(payload)
    unknown_payload["instructions"][0]["sprite"]["id"] = "unknown/sprite"
    unknown_payload["instructions"][0]["layer"] = "unknown/layer"

    caplog.clear()
    result_unknown = harness.replay(unknown_payload)
    assert len(caplog.records) == 2
    assert result_unknown.instructions[0].sprite is None
    assert result_unknown.instructions[0].layer is None


def test_audio_harness_routes_events_and_logs_unknown(caplog):
    manifest_payload = AudioEngine().build_manifest().to_dict()
    manifest = AudioManifestDTO.from_dict(manifest_payload)
    harness = AudioPlaybackHarness(manifest)

    asset_root = Path("assets")
    for descriptor in manifest.effects.values():
        assert (asset_root / descriptor.path).exists()
    for track in manifest.music.values():
        assert (asset_root / track.path).exists()

    caplog.set_level(logging.WARNING, logger="native.client.audio")
    frame = AudioFrameDTO.from_dict(_build_audio_payload())
    routed = harness.route(frame)

    assert routed.effects
    assert all(entry.clip is not None for entry in routed.effects)
    assert routed.music and routed.music[0].track is not None
    assert not caplog.records

    unknown_payload = _build_audio_payload()
    unknown_payload["effects"][0]["clip"]["id"] = "effects/missing"
    unknown_payload["effects"][0]["clip"]["path"] = "missing.ogg"
    unknown_payload["music"][0]["track"]["id"] = "music/missing"
    unknown_payload["music"][0]["track"]["path"] = "missing.ogg"

    caplog.clear()
    routed_unknown = harness.route_payload(unknown_payload)
    assert len(caplog.records) == 2
    assert routed_unknown.effects[0].clip is None
    assert routed_unknown.music[0].track is None
