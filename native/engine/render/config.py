"""Configuration helpers for the deferred renderer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping

from .model import (
    BloomSettings,
    LightingEnvironment,
    Light,
    MaterialDefinition,
    MaterialRegistry,
    PostProcessingSettings,
    ToneMappingSettings,
)
from .post import PostProcessingChain

DEFAULT_RENDER_CONFIG = Path("game/config/rendering.json")


@dataclass(frozen=True)
class RenderPipelineConfig:
    """Aggregated configuration for building the render graph."""

    material_registry: MaterialRegistry
    lighting: LightingEnvironment
    post_processing: PostProcessingSettings

    def build_post_chain(self) -> PostProcessingChain:
        return PostProcessingChain(self.post_processing)


def _coerce_color(payload: Iterable[float] | Mapping[str, Any], *, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if isinstance(payload, Mapping):
        r = float(payload.get("r", payload.get("x", default[0])))
        g = float(payload.get("g", payload.get("y", default[1])))
        b = float(payload.get("b", payload.get("z", default[2])))
    else:
        values = tuple(payload)
        if len(values) < 3:
            return default
        r, g, b = float(values[0]), float(values[1]), float(values[2])
    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b)),
    )


def _load_materials(payload: Mapping[str, Any]) -> MaterialRegistry:
    definitions: Dict[str, MaterialDefinition] = {}
    default = payload.get("default")
    materials_payload = payload.get("definitions", payload)
    if not isinstance(materials_payload, Mapping):
        raise TypeError("materials definitions must be a mapping")
    for name, entry in materials_payload.items():
        if not isinstance(entry, Mapping):
            continue
        albedo = _coerce_color(entry.get("albedo", (1.0, 1.0, 1.0)), default=(1.0, 1.0, 1.0))
        emissive = _coerce_color(entry.get("emissive", (0.0, 0.0, 0.0)), default=(0.0, 0.0, 0.0))
        metallic = float(entry.get("metallic", 0.0))
        roughness = float(entry.get("roughness", 1.0))
        extras_payload = entry.get("extras", {})
        extras: MutableMapping[str, float] = {}
        if isinstance(extras_payload, Mapping):
            extras.update({str(k): float(v) for k, v in extras_payload.items()})
        definitions[str(name)] = MaterialDefinition(
            name=str(name),
            albedo=albedo,
            metallic=metallic,
            roughness=roughness,
            emissive=emissive,
            extras=extras,
        )
    default_name: str | None = None
    if default is not None:
        candidate = str(default)
        if candidate in definitions:
            default_name = candidate
    return MaterialRegistry(definitions, default_material=default_name)


def _load_lighting(payload: Mapping[str, Any]) -> LightingEnvironment:
    ambient = _coerce_color(payload.get("ambient_color", (0.1, 0.1, 0.1)), default=(0.1, 0.1, 0.1))
    lights_payload = payload.get("lights", [])
    lights: list[Light] = []
    for index, entry in enumerate(lights_payload):
        if not isinstance(entry, Mapping):
            continue
        name = str(entry.get("name", f"light_{index}"))
        kind = str(entry.get("type", entry.get("kind", "directional"))).lower()
        color = _coerce_color(entry.get("color", (1.0, 1.0, 1.0)), default=(1.0, 1.0, 1.0))
        intensity = float(entry.get("intensity", 1.0))
        direction = None
        position = None
        radius = None
        if "direction" in entry:
            direction = _coerce_color(entry["direction"], default=(0.0, 0.0, -1.0))
        if "position" in entry:
            position = _coerce_color(entry["position"], default=(0.0, 0.0, 0.0))
        if "range" in entry:
            radius = float(entry.get("range", 0.0))
        lights.append(
            Light(
                name=name,
                kind=kind,
                color=color,
                intensity=intensity,
                direction=direction,
                position=position,
                range=radius,
            )
        )
    return LightingEnvironment(ambient_color=ambient, lights=tuple(lights))


def _load_post_processing(payload: Mapping[str, Any]) -> PostProcessingSettings:
    bloom_payload = payload.get("bloom", {})
    tone_payload = payload.get("tone_mapping", {})
    bloom = BloomSettings(
        enabled=bool(bloom_payload.get("enabled", False)),
        threshold=float(bloom_payload.get("threshold", 1.0)),
        intensity=float(bloom_payload.get("intensity", 0.0)),
        radius=float(bloom_payload.get("radius", 1.0)),
    )
    tone = ToneMappingSettings(
        operator=str(tone_payload.get("operator", "aces")),
        exposure=float(tone_payload.get("exposure", 1.0)),
    )
    return PostProcessingSettings(bloom=bloom, tone_mapping=tone)


def load_render_pipeline_config(path: Path | None = None) -> RenderPipelineConfig:
    """Load the render pipeline configuration from *path*."""

    target_path = path or DEFAULT_RENDER_CONFIG
    payload = json.loads(Path(target_path).read_text())
    materials = _load_materials(payload.get("materials", {}))
    lighting = _load_lighting(payload.get("lighting", {}))
    post_processing = _load_post_processing(payload.get("post_processing", {}))
    return RenderPipelineConfig(
        material_registry=materials,
        lighting=lighting,
        post_processing=post_processing,
    )


__all__ = [
    "DEFAULT_RENDER_CONFIG",
    "RenderPipelineConfig",
    "load_render_pipeline_config",
]
