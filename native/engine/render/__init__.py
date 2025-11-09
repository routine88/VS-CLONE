"""Rendering pipeline building blocks used by the native runtime."""

from __future__ import annotations

from .config import DEFAULT_RENDER_CONFIG, RenderPipelineConfig, load_render_pipeline_config
from .graph import RenderGraph
from .model import (
    AppliedRenderFrame,
    AppliedRenderInstruction,
    BloomSettings,
    GBuffer,
    GBufferSample,
    LightingEnvironment,
    LightingResult,
    LitSurface,
    MaterialDefinition,
    MaterialRegistry,
    PostProcessResult,
    PostProcessingSettings,
    ToneMappingSettings,
)

__all__ = [
    "AppliedRenderFrame",
    "AppliedRenderInstruction",
    "BloomSettings",
    "GBuffer",
    "GBufferSample",
    "LightingEnvironment",
    "LightingResult",
    "LitSurface",
    "MaterialDefinition",
    "MaterialRegistry",
    "PostProcessResult",
    "PostProcessingSettings",
    "RenderGraph",
    "RenderPipelineConfig",
    "ToneMappingSettings",
    "DEFAULT_RENDER_CONFIG",
    "load_render_pipeline_config",
]
