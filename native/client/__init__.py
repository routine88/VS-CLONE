"""Data transfer objects and utilities for consuming prototype exports."""

from .dto import RenderFrameDTO, RenderInstructionDTO, SpriteDescriptor
from .manifest import GraphicsManifest, LayerDefinition, ManifestSprite, SpriteRegistry
from .harness import FramePlaybackHarness, PlaybackFrame, ResolvedInstruction

__all__ = [
    "RenderFrameDTO",
    "RenderInstructionDTO",
    "SpriteDescriptor",
    "GraphicsManifest",
    "LayerDefinition",
    "ManifestSprite",
    "SpriteRegistry",
    "FramePlaybackHarness",
    "PlaybackFrame",
    "ResolvedInstruction",
]
