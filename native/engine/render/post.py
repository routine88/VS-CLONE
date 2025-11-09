"""Post-processing utilities for the deferred renderer."""

from __future__ import annotations

from typing import Sequence, Tuple

from .model import (
    BloomSettings,
    LitSurface,
    PostProcessResult,
    PostProcessingSettings,
    ToneMappingSettings,
)
from .passes import luminance

Color3 = tuple[float, float, float]


def _apply_tone_mapping(color: Color3, settings: ToneMappingSettings) -> Color3:
    exposure = max(0.001, settings.exposure)
    mapped = (color[0] * exposure, color[1] * exposure, color[2] * exposure)
    operator = settings.operator.lower()
    if operator == "reinhard":
        return tuple(channel / (1.0 + channel) for channel in mapped)  # type: ignore[return-value]
    if operator == "linear":
        return tuple(max(0.0, min(1.0, channel)) for channel in mapped)  # type: ignore[return-value]
    # Default to ACES filmic curve
    a = 2.51
    b = 0.03
    c = 2.43
    d = 0.59
    e = 0.14
    result = []
    for channel in mapped:
        value = (channel * (a * channel + b)) / (channel * (c * channel + d) + e)
        result.append(max(0.0, min(1.0, value)))
    return tuple(result)  # type: ignore[return-value]


def _apply_bloom(color: Color3, settings: BloomSettings) -> tuple[Color3, float]:
    if not settings.enabled:
        return color, 0.0
    threshold = settings.threshold
    strength = max(0.0, settings.intensity)
    brightness = luminance(color)
    if brightness <= threshold:
        return color, 0.0
    bloom_factor = (brightness - threshold) * strength
    bloom = (bloom_factor, bloom_factor, bloom_factor)
    combined = (color[0] + bloom[0], color[1] + bloom[1], color[2] + bloom[2])
    return combined, min(1.0, bloom_factor)


class PostProcessingChain:
    """Executes the configured post-processing pipeline."""

    def __init__(self, settings: PostProcessingSettings) -> None:
        self._settings = settings

    def apply(self, surfaces: Sequence[LitSurface]) -> PostProcessResult:
        final_colors: list[Color3] = []
        bloom_strength: list[float] = []
        for surface in surfaces:
            color, bloom = _apply_bloom(surface.color, self._settings.bloom)
            mapped = _apply_tone_mapping(color, self._settings.tone_mapping)
            final_colors.append(mapped)
            bloom_strength.append(bloom)
        return PostProcessResult(
            surfaces=tuple(surfaces),
            final_colors=tuple(final_colors),
            bloom_strength=tuple(bloom_strength),
            tone_mapping_operator=self._settings.tone_mapping.operator,
        )


__all__ = ["PostProcessingChain"]
