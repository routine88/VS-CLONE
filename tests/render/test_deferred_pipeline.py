from __future__ import annotations

import json
from pathlib import Path

import pytest

from native.client.dto import RenderFrameDTO, RenderInstructionDTO, SpriteDescriptor
from native.engine.render import RenderGraph, load_render_pipeline_config
from native.engine.render.passes import luminance
from native.runtime.assets import SpriteRegistry

SNAPSHOT_PATH = Path("tests/render/snapshots/deferred_colors.json")


def _build_instruction(
    sprite: SpriteDescriptor,
    *,
    node_id: str,
    metadata: dict[str, object] | None = None,
) -> RenderInstructionDTO:
    return RenderInstructionDTO(
        node_id=node_id,
        sprite=sprite,
        position=(0.0, 0.0),
        scale=1.0,
        rotation=0.0,
        flip_x=False,
        flip_y=False,
        layer="default",
        z_index=0,
        metadata=metadata or {},
    )


@pytest.fixture(scope="module")
def sprite_descriptor() -> SpriteDescriptor:
    registry = SpriteRegistry()
    sprite = next(iter(registry.manifest.sprites.values()))
    return sprite.to_sprite_descriptor()


@pytest.fixture()
def render_graph() -> RenderGraph:
    config = load_render_pipeline_config()
    return RenderGraph(config)


@pytest.fixture()
def sprite_registry() -> SpriteRegistry:
    return SpriteRegistry()


def test_deferred_lighting_respects_normals(
    render_graph: RenderGraph, sprite_registry: SpriteRegistry, sprite_descriptor: SpriteDescriptor
) -> None:
    front_instruction = _build_instruction(
        sprite_descriptor,
        node_id="front",
        metadata={"normal": (0.0, 0.0, 1.0)},
    )
    back_instruction = _build_instruction(
        sprite_descriptor,
        node_id="back",
        metadata={"normal": (0.0, 0.0, -1.0)},
    )
    frame = RenderFrameDTO(
        time=0.0,
        viewport=(1920, 1080),
        instructions=(front_instruction, back_instruction),
        messages=tuple(),
    )

    applied, missing = render_graph.apply(frame, sprite_registry.resolve)

    assert missing == 0
    assert len(applied.lighting.surfaces) == 2

    front_surface = next(surface for surface in applied.lighting.surfaces if surface.sample.applied.instruction.node_id == "front")
    back_surface = next(surface for surface in applied.lighting.surfaces if surface.sample.applied.instruction.node_id == "back")

    assert luminance(front_surface.color) > luminance(back_surface.color)
    assert applied.post_process.tone_mapping_operator.lower() == "aces"


def test_post_processing_applies_bloom_for_emissive_materials(
    render_graph: RenderGraph, sprite_registry: SpriteRegistry, sprite_descriptor: SpriteDescriptor
) -> None:
    default_instruction = _build_instruction(
        sprite_descriptor,
        node_id="default",
        metadata={"material": "default_lit"},
    )
    emissive_instruction = _build_instruction(
        sprite_descriptor,
        node_id="glow",
        metadata={"material": "emissive_ui", "emissive": (1.0, 1.0, 1.0)},
    )
    frame = RenderFrameDTO(
        time=0.1,
        viewport=(1920, 1080),
        instructions=(default_instruction, emissive_instruction),
        messages=("lighting",),
    )

    applied, _ = render_graph.apply(frame, sprite_registry.resolve)
    strengths = {
        surface.sample.applied.instruction.node_id: bloom
        for surface, bloom in zip(applied.post_process.surfaces, applied.post_process.bloom_strength)
    }
    assert strengths["glow"] > strengths["default"]
    assert strengths["glow"] > 0.0


def test_render_pipeline_snapshot(
    render_graph: RenderGraph, sprite_registry: SpriteRegistry, sprite_descriptor: SpriteDescriptor
) -> None:
    instructions = (
        _build_instruction(
            sprite_descriptor,
            node_id="baseline",
            metadata={"material": "default_lit", "normal": (0.0, 0.0, 1.0)},
        ),
        _build_instruction(
            sprite_descriptor,
            node_id="rim_lit",
            metadata={"material": "terrain", "normal": (0.0, 1.0, 0.0)},
        ),
        _build_instruction(
            sprite_descriptor,
            node_id="emissive",
            metadata={"material": "emissive_ui", "emissive": (0.8, 0.8, 0.9)},
        ),
    )
    frame = RenderFrameDTO(
        time=0.2,
        viewport=(1920, 1080),
        instructions=instructions,
        messages=("snapshot",),
    )
    applied, _ = render_graph.apply(frame, sprite_registry.resolve)
    final_colors = [list(color) for color in applied.post_process.final_colors]

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert len(expected) == len(final_colors)
    for observed, baseline in zip(final_colors, expected):
        assert pytest.approx(observed[0], rel=1e-3, abs=1e-4) == baseline[0]
        assert pytest.approx(observed[1], rel=1e-3, abs=1e-4) == baseline[1]
        assert pytest.approx(observed[2], rel=1e-3, abs=1e-4) == baseline[2]
