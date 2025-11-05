"""Data transfer objects and utilities for consuming prototype exports."""

from .audio import (
    AudioFrameDTO,
    AudioManifestDTO,
    AudioPlaybackFrame,
    AudioPlaybackHarness,
    MusicInstructionDTO,
    MusicTrackDescriptor,
    ResolvedEffectInstruction,
    ResolvedMusicInstruction,
    SoundClipDescriptor,
    SoundInstructionDTO,
)
from .dto import RenderFrameDTO, RenderInstructionDTO, SpriteDescriptor
from .harness import FramePlaybackHarness, PlaybackFrame, ResolvedInstruction
from .manifest import GraphicsManifest, LayerDefinition, ManifestSprite, SpriteRegistry

__all__ = [
    "AudioFrameDTO",
    "AudioManifestDTO",
    "AudioPlaybackFrame",
    "AudioPlaybackHarness",
    "MusicInstructionDTO",
    "MusicTrackDescriptor",
    "SoundClipDescriptor",
    "SoundInstructionDTO",
    "ResolvedEffectInstruction",
    "ResolvedMusicInstruction",
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
