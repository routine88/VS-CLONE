import copy
import logging
from pathlib import Path

from game.export import EngineFrameExporter
from game.graphics import GraphicsEngine, SceneNode
from game.graphics_assets import load_asset_manifest

from native.client import FramePlaybackHarness, GraphicsManifest, RenderFrameDTO

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
