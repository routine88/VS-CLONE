from pathlib import Path

from game.graphics import GraphicsEngine
from game.graphics_assets import load_asset_manifest


ASSET_ROOT = Path("assets/graphics_assets")


def test_manifest_loads_and_registers_with_engine():
    manifest = load_asset_manifest(ASSET_ROOT / "manifest.json")
    engine = GraphicsEngine(viewport=(320, 180))

    # ensure viewport override occurs when requested
    assert engine.viewport == (320, 180)
    manifest.apply(engine, replace_existing=True, update_viewport=True)
    assert engine.viewport == manifest.viewport

    # spot check that key sprites and placeholders were registered
    player_sprite = engine.sprite("placeholders/player")
    assert player_sprite.texture == "sprites/player_placeholder.texture.json"
    assert engine.build_manifest().placeholders["player"] == "placeholders/player"


def test_placeholder_textures_match_manifest_dimensions():
    manifest = load_asset_manifest(ASSET_ROOT / "manifest.json")
    warnings = manifest.validate_assets(ASSET_ROOT)
    assert not warnings, f"asset validation emitted warnings: {warnings}"
