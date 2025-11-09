"""Data models shared by the deferred rendering pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Dict, Iterable, Mapping, MutableMapping, Sequence, Tuple

from native.client.dto import RenderFrameDTO, RenderInstructionDTO

if TYPE_CHECKING:
    from native.runtime.assets import SpriteHandle

Color3 = Tuple[float, float, float]
Vector3 = Tuple[float, float, float]


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _normalise_color(values: Iterable[float] | Mapping[str, float]) -> Color3:
    if isinstance(values, Mapping):
        r = float(values.get("r", values.get("x", 0.0)))
        g = float(values.get("g", values.get("y", 0.0)))
        b = float(values.get("b", values.get("z", 0.0)))
    else:
        sequence = tuple(values)
        if len(sequence) < 3:
            raise ValueError("Color requires at least three components")
        r, g, b = float(sequence[0]), float(sequence[1]), float(sequence[2])
    return (_clamp(r), _clamp(g), _clamp(b))


def _normalise_vector(values: Iterable[float] | Mapping[str, float], *, default: Vector3) -> Vector3:
    if isinstance(values, Mapping):
        x = float(values.get("x", values.get("r", default[0])))
        y = float(values.get("y", values.get("g", default[1])))
        z = float(values.get("z", values.get("b", default[2])))
    else:
        sequence = tuple(values)
        if len(sequence) < 3:
            return default
        x, y, z = float(sequence[0]), float(sequence[1]), float(sequence[2])
    length = (x * x + y * y + z * z) ** 0.5
    if length <= 1e-8:
        return default
    return (x / length, y / length, z / length)


def _normalise_scalar(value: object, *, default: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return _clamp(numeric, minimum, maximum)


@dataclass(frozen=True)
class MaterialDefinition:
    """Configurable shading parameters for sprites."""

    name: str
    albedo: Color3
    metallic: float = 0.0
    roughness: float = 1.0
    emissive: Color3 = (0.0, 0.0, 0.0)
    extras: Mapping[str, float] = field(default_factory=dict)

    def with_overrides(
        self,
        *,
        albedo: Color3 | None = None,
        metallic: float | None = None,
        roughness: float | None = None,
        emissive: Color3 | None = None,
        extras: Mapping[str, float] | None = None,
    ) -> "MaterialDefinition":
        payload: Dict[str, float] = dict(self.extras)
        if extras:
            payload.update({str(key): float(value) for key, value in extras.items()})
        return replace(
            self,
            albedo=albedo or self.albedo,
            metallic=self.metallic if metallic is None else float(metallic),
            roughness=self.roughness if roughness is None else float(roughness),
            emissive=emissive or self.emissive,
            extras=payload,
        )


class MaterialRegistry:
    """Lookup table that resolves material definitions for draw calls."""

    def __init__(self, materials: Mapping[str, MaterialDefinition], *, default_material: str | None = None) -> None:
        if not materials:
            raise ValueError("At least one material definition must be provided")
        self._materials = dict(materials)
        if default_material is None:
            default_material = next(iter(self._materials))
        if default_material not in self._materials:
            raise KeyError(f"Unknown default material '{default_material}'")
        self._default = default_material

    @property
    def default(self) -> MaterialDefinition:
        return self._materials[self._default]

    def resolve(self, name: str | None) -> MaterialDefinition:
        if name:
            material = self._materials.get(name)
            if material is not None:
                return material
        return self.default

    def resolve_for_instruction(self, applied: "AppliedRenderInstruction") -> MaterialDefinition:
        metadata = applied.instruction.metadata
        manifest = applied.sprite.manifest
        preferred = metadata.get("material")
        if preferred is None and manifest is not None:
            preferred = manifest.lighting or None
        material = self.resolve(preferred)

        overrides = metadata.get("material_overrides")
        extra_overrides = metadata.get("material_extras")

        albedo_override = metadata.get("albedo")
        emissive_override = metadata.get("emissive")
        metallic_override = metadata.get("metallic")
        roughness_override = metadata.get("roughness")

        albedo: Color3 | None = None
        emissive: Color3 | None = None
        metallic: float | None = None
        roughness: float | None = None
        extra_payload: MutableMapping[str, float] | None = None

        if albedo_override is not None:
            albedo = _normalise_color(albedo_override)
        if emissive_override is not None:
            emissive = _normalise_color(emissive_override)
        if metallic_override is not None:
            metallic = _normalise_scalar(metallic_override, default=material.metallic)
        if roughness_override is not None:
            roughness = _normalise_scalar(roughness_override, default=material.roughness)
        if isinstance(overrides, Mapping):
            if "albedo" in overrides and albedo is None:
                albedo = _normalise_color(overrides["albedo"])  # type: ignore[arg-type]
            if "emissive" in overrides and emissive is None:
                emissive = _normalise_color(overrides["emissive"])  # type: ignore[arg-type]
            if "metallic" in overrides and metallic is None:
                metallic = _normalise_scalar(overrides["metallic"], default=material.metallic)  # type: ignore[arg-type]
            if "roughness" in overrides and roughness is None:
                roughness = _normalise_scalar(overrides["roughness"], default=material.roughness)  # type: ignore[arg-type]
            extra_payload = {str(k): float(v) for k, v in overrides.items() if k not in {"albedo", "emissive", "metallic", "roughness"}}

        if isinstance(extra_overrides, Mapping):
            if extra_payload is None:
                extra_payload = {}
            extra_payload.update({str(k): float(v) for k, v in extra_overrides.items()})

        return material.with_overrides(
            albedo=albedo,
            emissive=emissive,
            metallic=metallic,
            roughness=roughness,
            extras=extra_payload,
        )


@dataclass(frozen=True)
class AppliedRenderInstruction:
    """Render instruction paired with the resolved sprite handle."""

    instruction: RenderInstructionDTO
    sprite: "SpriteHandle"


@dataclass(frozen=True)
class GBufferSample:
    """Result produced by the G-buffer pass for a single instruction."""

    applied: AppliedRenderInstruction
    material: MaterialDefinition
    albedo: Color3
    normal: Vector3
    emissive: Color3
    metallic: float
    roughness: float
    depth: float
    world_position: Vector3


@dataclass(frozen=True)
class GBuffer:
    """Collection of deferred shading inputs for the lighting pass."""

    samples: Tuple[GBufferSample, ...]

    def __iter__(self) -> Iterable[GBufferSample]:
        return iter(self.samples)

    def __len__(self) -> int:
        return len(self.samples)


@dataclass(frozen=True)
class Light:
    """Light definition used by the lighting pass."""

    name: str
    kind: str
    color: Color3
    intensity: float
    direction: Vector3 | None = None
    position: Vector3 | None = None
    range: float | None = None


@dataclass(frozen=True)
class LightingEnvironment:
    """Ambient lighting configuration for the scene."""

    ambient_color: Color3
    lights: Tuple[Light, ...] = tuple()


@dataclass(frozen=True)
class LightingContribution:
    """Individual light contribution recorded for debugging."""

    light: str
    intensity: float


@dataclass(frozen=True)
class LitSurface:
    """Lighting result associated with a surface in the frame."""

    sample: GBufferSample
    color: Color3
    contributions: Tuple[LightingContribution, ...]


@dataclass(frozen=True)
class LightingResult:
    """Aggregated lighting output for a frame."""

    surfaces: Tuple[LitSurface, ...]
    ambient_color: Color3


@dataclass(frozen=True)
class BloomSettings:
    enabled: bool = False
    threshold: float = 1.0
    intensity: float = 0.0
    radius: float = 1.0


@dataclass(frozen=True)
class ToneMappingSettings:
    operator: str = "aces"
    exposure: float = 1.0


@dataclass(frozen=True)
class PostProcessingSettings:
    bloom: BloomSettings = BloomSettings()
    tone_mapping: ToneMappingSettings = ToneMappingSettings()


@dataclass(frozen=True)
class PostProcessResult:
    """Final composited output produced by the post-processing chain."""

    surfaces: Tuple[LitSurface, ...]
    final_colors: Tuple[Color3, ...]
    bloom_strength: Tuple[float, ...]
    tone_mapping_operator: str


@dataclass(frozen=True)
class AppliedRenderFrame:
    """Combined result from all render graph passes."""

    frame: RenderFrameDTO
    instructions: Tuple[AppliedRenderInstruction, ...]
    gbuffer: GBuffer
    lighting: LightingResult
    post_process: PostProcessResult


__all__ = [
    "AppliedRenderFrame",
    "AppliedRenderInstruction",
    "BloomSettings",
    "GBuffer",
    "GBufferSample",
    "Light",
    "LightingContribution",
    "LightingEnvironment",
    "LightingResult",
    "LitSurface",
    "MaterialDefinition",
    "MaterialRegistry",
    "PostProcessResult",
    "PostProcessingSettings",
    "ToneMappingSettings",
]
