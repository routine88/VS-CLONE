from game.graphics import (
    AnimationClip,
    AnimationFrame,
    Camera,
    GraphicsManifest,
    GraphicsEngine,
    LayerSettings,
    SceneNode,
    Sprite,
)
from game.interactive import ArcadeEngine, InputFrame, Projectile


def test_graphics_engine_animation_and_layer_sorting():
    graphics = GraphicsEngine(viewport=(640, 360))
    graphics.register_layer(LayerSettings(name="background.sky", z_index=-5, parallax=0.2))
    graphics.register_layer(LayerSettings(name="actors.hero", z_index=25, parallax=1.0))

    graphics.register_sprite(
        Sprite(id="hero_idle", texture="sprites/hero_idle.png", size=(64, 64))
    )
    graphics.register_sprite(
        Sprite(id="hero_run", texture="sprites/hero_run.png", size=(64, 64))
    )
    graphics.register_animation(
        AnimationClip(
            id="hero.run",
            frames=(
                AnimationFrame(sprite_id="hero_idle", duration=0.2),
                AnimationFrame(sprite_id="hero_run", duration=0.2),
            ),
        )
    )

    nodes = [
        SceneNode(
            id="bg",
            position=(0.0, 0.0),
            layer="background.sky",
            sprite_id="placeholders/background",
            metadata={"kind": "background"},
        ),
        SceneNode(
            id="hero",
            position=(6.0, 1.0),
            layer="actors.hero",
            animation_id="hero.run",
            metadata={"kind": "player"},
        ),
    ]

    frame = graphics.build_frame(nodes, camera=Camera(position=(0.0, 0.0), viewport=(640, 360)), time=0.25)

    assert [instruction.node_id for instruction in frame.instructions] == ["bg", "hero"]
    hero_instruction = next(instr for instr in frame.instructions if instr.node_id == "hero")
    assert hero_instruction.sprite.id == "hero_run"
    assert hero_instruction.position[0] > frame.viewport[0] * 0.5


def test_graphics_engine_placeholder_resolution():
    graphics = GraphicsEngine()
    node = SceneNode(
        id="enemy",
        position=(0.0, 0.0),
        layer="actors",
        sprite_id="enemies/unknown",
        metadata={"kind": "enemy"},
    )

    frame = graphics.build_frame([node])
    assert frame.instructions[0].sprite.id == "placeholders/enemy"


def test_arcade_engine_render_frame_bridge():
    engine = ArcadeEngine(spawn_interval=10.0, target_duration=30.0)
    engine._projectiles.append(Projectile(x=6.0, y=engine.height / 2.0, speed=0.0, damage=6.0))
    snapshot = engine.step(0.1, InputFrame())

    nodes = engine.build_scene_nodes(snapshot)
    kinds = {node.kind for node in nodes}
    assert "player" in kinds
    assert "background" in kinds
    assert any(node.kind == "projectile" for node in nodes)

    graphics = GraphicsEngine()
    render_frame = engine.render_frame(graphics, snapshot=snapshot)

    assert render_frame.messages == tuple(snapshot.messages)
    assert any(instr.metadata.get("kind") == "player" for instr in render_frame.instructions)


def test_graphics_manifest_export():
    graphics = GraphicsEngine()
    manifest = graphics.build_manifest()
    assert isinstance(manifest, GraphicsManifest)

    manifest_dict = manifest.to_dict()
    assert manifest_dict["viewport"] == [1280, 720]
    assert manifest_dict["sprites"]["placeholders/player"]["size"] == [96, 96]
    assert manifest_dict["placeholders"]["player"] == "placeholders/player"
    assert "actors" in manifest_dict["layers"]
