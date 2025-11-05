"""Data transfer objects and utilities for consuming prototype exports."""

from .audio import (
    AppliedAudioFrame,
    AudioFrameDTO,
    AudioManifestDTO,
    AudioMixer,
    AudioPlaybackFrame,
    AudioPlaybackHarness,
    EffectPlaybackEvent,
    MusicInstructionDTO,
    MusicPlaybackEvent,
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
    "AppliedAudioFrame",
    "AudioFrameDTO",
    "AudioManifestDTO",
    "AudioMixer",
    "AudioPlaybackFrame",
    "AudioPlaybackHarness",
    "EffectPlaybackEvent",
    "MusicInstructionDTO",
    "MusicPlaybackEvent",
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
