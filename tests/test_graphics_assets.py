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


def test_manifest_application_respects_replace_existing_placeholders():
    manifest = load_asset_manifest(ASSET_ROOT / "manifest.json")
    engine = GraphicsEngine()

    original_placeholders = engine.build_manifest().placeholders
    manifest.apply(engine, replace_existing=False, update_viewport=False)

    updated_placeholders = engine.build_manifest().placeholders
    assert updated_placeholders == original_placeholders


def test_manifest_application_registers_expected_sprites():
    manifest = load_asset_manifest(ASSET_ROOT / "manifest.json")
    engine = GraphicsEngine()

    manifest.apply(engine, replace_existing=True, update_viewport=False)

    health_orb = engine.sprite("sprites/ui/health_orb")
    dash_trail = engine.sprite("sprites/effects/dash_trail")
    soul_counter = engine.sprite("sprites/ui/soul_counter")
    boss_placeholder = engine.sprite("placeholders/boss")

    assert health_orb.texture == "sprites/ui/health_orb.texture.json"
    assert health_orb.size == (64, 64)
    assert dash_trail.texture == "sprites/effects/dash_trail.texture.json"
    assert dash_trail.size == (128, 64)
    assert soul_counter.size == (160, 128)
    assert boss_placeholder.size == (192, 192)
