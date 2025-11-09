"""Render passes that compose the deferred shading pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .model import (
    AppliedRenderInstruction,
    GBuffer,
    GBufferSample,
    Light,
    LightingContribution,
    LightingEnvironment,
    LightingResult,
    LitSurface,
    MaterialDefinition,
    MaterialRegistry,
)

Vector3 = tuple[float, float, float]
Color3 = tuple[float, float, float]


def _sprite_tint(applied: AppliedRenderInstruction) -> Color3:
    tint = applied.sprite.tint
    if tint is None:
        return (1.0, 1.0, 1.0)
    return tuple(channel / 255.0 for channel in tint)


def _multiply_color(a: Color3, b: Color3) -> Color3:
    return (a[0] * b[0], a[1] * b[1], a[2] * b[2])


def _add_color(a: Color3, b: Color3) -> Color3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale_color(color: Color3, scale: float) -> Color3:
    return (color[0] * scale, color[1] * scale, color[2] * scale)


def _clamp_color(color: Color3) -> Color3:
    return (max(0.0, min(1.0, color[0])), max(0.0, min(1.0, color[1])), max(0.0, min(1.0, color[2])))


def _dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _subtract(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _length(vec: Vector3) -> float:
    return (vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2) ** 0.5


def _normal_from_instruction(applied: AppliedRenderInstruction) -> Vector3:
    metadata = applied.instruction.metadata
    normal_payload = metadata.get("normal")
    if normal_payload is not None:
        try:
            x, y, z = float(normal_payload[0]), float(normal_payload[1]), float(normal_payload[2])  # type: ignore[index]
        except (TypeError, ValueError, IndexError):
            pass
        else:
            length = (x * x + y * y + z * z) ** 0.5
            if length > 1e-8:
                return (x / length, y / length, z / length)
    rotation = applied.instruction.rotation
    return (
        0.0,
        0.0,
        1.0,
    )


def _world_position(applied: AppliedRenderInstruction) -> Vector3:
    x, y = applied.instruction.position
    z = float(applied.instruction.metadata.get("depth", applied.instruction.z_index))
    return (float(x), float(y), z)


def _resolve_albedo(material: MaterialDefinition, applied: AppliedRenderInstruction) -> Color3:
    base = material.albedo
    tint = _sprite_tint(applied)
    albedo = _multiply_color(base, tint)
    metadata = applied.instruction.metadata
    override = metadata.get("albedo")
    if isinstance(override, Sequence) and len(override) >= 3:
        try:
            albedo = (float(override[0]), float(override[1]), float(override[2]))  # type: ignore[index]
        except (TypeError, ValueError):
            pass
    return (
        max(0.0, min(1.0, albedo[0])),
        max(0.0, min(1.0, albedo[1])),
        max(0.0, min(1.0, albedo[2])),
    )


def _resolve_emissive(material: MaterialDefinition, applied: AppliedRenderInstruction) -> Color3:
    override = applied.instruction.metadata.get("emissive")
    if isinstance(override, Sequence) and len(override) >= 3:
        try:
            emissive = (float(override[0]), float(override[1]), float(override[2]))  # type: ignore[index]
        except (TypeError, ValueError):
            emissive = material.emissive
    else:
        emissive = material.emissive
    return emissive


class GBufferPass:
    """Produces deferred shading inputs from resolved instructions."""

    def __init__(self, materials: MaterialRegistry) -> None:
        self._materials = materials

    def build(self, instructions: Sequence[AppliedRenderInstruction]) -> GBuffer:
        samples: list[GBufferSample] = []
        for applied in instructions:
            material = self._materials.resolve_for_instruction(applied)
            albedo = _resolve_albedo(material, applied)
            emissive = _resolve_emissive(material, applied)
            normal = _normal_from_instruction(applied)
            depth = float(applied.instruction.metadata.get("depth", applied.instruction.z_index))
            world = _world_position(applied)
            samples.append(
                GBufferSample(
                    applied=applied,
                    material=material,
                    albedo=albedo,
                    normal=normal,
                    emissive=emissive,
                    metallic=material.metallic,
                    roughness=material.roughness,
                    depth=depth,
                    world_position=world,
                )
            )
        return GBuffer(samples=tuple(samples))


def _apply_directional_light(sample: GBufferSample, light: Light) -> tuple[Color3, float]:
    if light.direction is None:
        return ((0.0, 0.0, 0.0), 0.0)
    direction = (-light.direction[0], -light.direction[1], -light.direction[2])
    ndotl = max(0.0, _dot(sample.normal, direction))
    intensity = light.intensity * ndotl
    return (_scale_color(light.color, intensity), intensity)


def _apply_point_light(sample: GBufferSample, light: Light) -> tuple[Color3, float]:
    if light.position is None or light.range in (None, 0):
        return ((0.0, 0.0, 0.0), 0.0)
    to_light = _subtract(light.position, sample.world_position)
    distance = _length(to_light)
    if distance <= 1e-5:
        attenuation = 1.0
        direction = (0.0, 0.0, 1.0)
    else:
        direction = (to_light[0] / distance, to_light[1] / distance, to_light[2] / distance)
        attenuation = max(0.0, 1.0 - distance / float(light.range))
    ndotl = max(0.0, _dot(sample.normal, direction))
    intensity = light.intensity * attenuation * ndotl
    return (_scale_color(light.color, intensity), intensity)


class LightingPass:
    """Computes lighting contributions from the deferred inputs."""

    def __init__(self, environment: LightingEnvironment) -> None:
        self._environment = environment

    @staticmethod
    def _shade_sample(sample: GBufferSample, environment: LightingEnvironment) -> LitSurface:
        base_color = _multiply_color(sample.albedo, environment.ambient_color)
        contributions: list[LightingContribution] = []
        lit_color = base_color
        for light in environment.lights:
            if light.kind == "directional":
                added, intensity = _apply_directional_light(sample, light)
            elif light.kind == "point":
                added, intensity = _apply_point_light(sample, light)
            else:
                continue
            if intensity <= 0.0:
                continue
            lit_color = _add_color(lit_color, _multiply_color(sample.albedo, added))
            contributions.append(LightingContribution(light=light.name, intensity=intensity))
        lit_color = _add_color(lit_color, sample.emissive)
        lit_color = _clamp_color(lit_color)
        return LitSurface(sample=sample, color=lit_color, contributions=tuple(contributions))

    def shade(self, gbuffer: GBuffer) -> LightingResult:
        surfaces = tuple(self._shade_sample(sample, self._environment) for sample in gbuffer)
        return LightingResult(surfaces=surfaces, ambient_color=self._environment.ambient_color)


def luminance(color: Color3) -> float:
    r, g, b = color
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


__all__ = [
    "GBufferPass",
    "LightingPass",
    "luminance",
]
