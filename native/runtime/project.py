"""Renderer project scaffolding for ingesting exported runtime frames."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from native.client.audio import AudioFrameDTO, MusicInstructionDTO
from native.client.dto import RenderFrameDTO
from native.engine.render import (
    DEFAULT_RENDER_CONFIG,
    AppliedRenderFrame,
    RenderGraph,
    RenderPipelineConfig,
    load_render_pipeline_config,
)

from .assets import AudioRegistry, EffectHandle, MusicHandle, SpriteRegistry

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppliedAudioFrame:
    """Resolved audio frame ready for playback."""

    frame: AudioFrameDTO | None
    effects: tuple[EffectHandle, ...]
    music: tuple[tuple[MusicInstructionDTO, MusicHandle | None], ...]


@dataclass(frozen=True)
class AppliedFrame:
    """Combined result from render and audio processing."""

    render: AppliedRenderFrame
    audio: AppliedAudioFrame
    overrides: Mapping[str, object]


@dataclass
class Telemetry:
    """Aggregate metrics collected during playback."""

    render_frames: int = 0
    audio_frames: int = 0
    missing_sprites: int = 0
    missing_effects: int = 0
    missing_music: int = 0
    messages: int = 0
    overrides_applied: int = 0

    def record_render(self, applied: AppliedRenderFrame, *, missing: int) -> None:
        self.render_frames += 1
        self.messages += len(applied.frame.messages)
        self.missing_sprites += missing

    def record_audio(self, applied: AppliedAudioFrame, *, missing_effects: int, missing_music: int) -> None:
        if applied.frame is not None:
            self.audio_frames += 1
        self.missing_effects += missing_effects
        self.missing_music += missing_music

    def record_override(self) -> None:
        self.overrides_applied += 1


class RendererWindow:
    """Trivial window abstraction used for viewport validation."""

    def __init__(self) -> None:
        self.viewport = (0, 0)
        self.last_time = 0.0

    def apply_frame(self, frame: RenderFrameDTO) -> None:
        self.viewport = frame.viewport
        self.last_time = frame.time


class AudioMixer:
    """Resolves audio instructions via the audio registry."""

    def __init__(self, registry: AudioRegistry, *, logger: logging.Logger | None = None) -> None:
        self._registry = registry
        self._logger = logger or LOGGER

    def apply(self, frame: AudioFrameDTO | None) -> tuple[AppliedAudioFrame, int, int]:
        if frame is None:
            applied = AppliedAudioFrame(frame=None, effects=tuple(), music=tuple())
            return applied, 0, 0

        missing_effects = 0
        missing_music = 0

        effects: list[EffectHandle] = []
        for instruction in frame.effects:
            handle = self._registry.resolve_effect_instruction(instruction)
            if instruction.clip.id and handle.descriptor.id != instruction.clip.id:
                # Fallback indicates a missing manifest entry.
                missing_effects += 1
            effects.append(handle)

        music_entries: list[tuple[MusicInstructionDTO, MusicHandle | None]] = []
        for instruction in frame.music:
            handle = self._registry.resolve_music_instruction(instruction)
            if instruction.track is not None and handle is None:
                missing_music += 1
                self._logger.warning("Missing music track %s", instruction.track.id)
            music_entries.append((instruction, handle))

        applied = AppliedAudioFrame(
            frame=frame,
            effects=tuple(effects),
            music=tuple(music_entries),
        )
        return applied, missing_effects, missing_music


class InputLayer:
    """Captures runtime input overrides injected during playback."""

    def __init__(self) -> None:
        self._last_override: Mapping[str, object] = {}

    def apply(self, overrides: Mapping[str, object] | None) -> Mapping[str, object]:
        if overrides is None:
            self._last_override = {}
        else:
            self._last_override = dict(overrides)
        return self._last_override

    @property
    def last_override(self) -> Mapping[str, object]:
        return self._last_override


class RendererProject:
    """High-level orchestrator that applies frames to runtime systems."""

    def __init__(
        self,
        *,
        sprite_registry: SpriteRegistry,
        audio_registry: AudioRegistry,
        logger: logging.Logger | None = None,
        render_config_path: Path | None = None,
        pipeline_config: RenderPipelineConfig | None = None,
    ) -> None:
        self._logger = logger or LOGGER
        self._sprite_registry = sprite_registry
        self._audio_registry = audio_registry
        self._window = RendererWindow()
        if pipeline_config is None:
            config_path = Path(render_config_path or DEFAULT_RENDER_CONFIG)
            pipeline_config = load_render_pipeline_config(config_path)
        else:
            config_path = Path(render_config_path or DEFAULT_RENDER_CONFIG)
        self._render_config_path = config_path
        self._pipeline_config = pipeline_config
        self._render_graph = RenderGraph(pipeline_config, logger=self._logger)
        self._audio_mixer = AudioMixer(audio_registry, logger=self._logger)
        self._input_layer = InputLayer()
        self._telemetry = Telemetry()

    @property
    def telemetry(self) -> Telemetry:
        return self._telemetry

    @property
    def window(self) -> RendererWindow:
        return self._window

    @property
    def sprite_registry(self) -> SpriteRegistry:
        return self._sprite_registry

    @property
    def audio_registry(self) -> AudioRegistry:
        return self._audio_registry

    @property
    def pipeline_config(self) -> RenderPipelineConfig:
        return self._pipeline_config

    def apply_frame(
        self,
        render_frame: RenderFrameDTO,
        audio_frame: AudioFrameDTO | None,
        *,
        overrides: Mapping[str, object] | None = None,
    ) -> AppliedFrame:
        self._window.apply_frame(render_frame)
        applied_render, missing_sprites = self._render_graph.apply(
            render_frame, self._sprite_registry.resolve
        )
        applied_audio, missing_effects, missing_music = self._audio_mixer.apply(audio_frame)

        override_payload = self._input_layer.apply(overrides)
        if override_payload:
            self._telemetry.record_override()

        self._telemetry.record_render(applied_render, missing=missing_sprites)
        self._telemetry.record_audio(
            applied_audio,
            missing_effects=missing_effects,
            missing_music=missing_music,
        )

        return AppliedFrame(
            render=applied_render,
            audio=applied_audio,
            overrides=override_payload,
        )


__all__ = [
    "AppliedAudioFrame",
    "AppliedFrame",
    "AppliedRenderFrame",
    "AudioMixer",
    "InputLayer",
    "RendererProject",
    "RendererWindow",
    "Telemetry",
]

