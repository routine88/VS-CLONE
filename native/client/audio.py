"""Audio DTOs and playback helpers for the native runtime."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SoundClipDescriptor:
    """Description of a short sound effect clip."""

    id: str
    path: str
    volume: float
    description: str
    tags: Tuple[str, ...]
    length_seconds: Optional[float]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SoundClipDescriptor":
        return cls(
            id=str(payload.get("id", "")),
            path=str(payload.get("path", "")),
            volume=float(payload.get("volume", 1.0)),
            description=str(payload.get("description", "")),
            tags=_tuple_of_strings(payload.get("tags")),
            length_seconds=_optional_float(payload.get("length_seconds")),
        )


@dataclass(frozen=True)
class MusicTrackDescriptor:
    """Description of a music asset referenced by the runtime."""

    id: str
    path: str
    volume: float
    loop: bool
    description: str
    tags: Tuple[str, ...]
    length_seconds: Optional[float]
    tempo_bpm: Optional[float]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MusicTrackDescriptor":
        return cls(
            id=str(payload.get("id", "")),
            path=str(payload.get("path", "")),
            volume=float(payload.get("volume", 1.0)),
            loop=bool(payload.get("loop", True)),
            description=str(payload.get("description", "")),
            tags=_tuple_of_strings(payload.get("tags")),
            length_seconds=_optional_float(payload.get("length_seconds")),
            tempo_bpm=_optional_float(payload.get("tempo_bpm")),
        )


@dataclass(frozen=True)
class SoundInstructionDTO:
    """Instruction to play a sound effect during a frame."""

    clip: SoundClipDescriptor
    volume: float
    pan: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SoundInstructionDTO":
        clip_payload = payload.get("clip", {})
        return cls(
            clip=SoundClipDescriptor.from_dict(clip_payload),
            volume=float(payload.get("volume", 1.0)),
            pan=float(payload.get("pan", 0.0)),
        )


@dataclass(frozen=True)
class MusicInstructionDTO:
    """Instruction to update the music playback state."""

    track: Optional[MusicTrackDescriptor]
    action: str
    volume: Optional[float]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MusicInstructionDTO":
        track_payload = payload.get("track")
        track = (
            None
            if track_payload is None
            else MusicTrackDescriptor.from_dict(track_payload)
        )
        volume: Optional[float]
        if "volume" in payload and payload["volume"] is not None:
            volume = float(payload["volume"])
        else:
            volume = None
        return cls(
            track=track,
            action=str(payload.get("action", "")),
            volume=volume,
        )


@dataclass(frozen=True)
class AudioFrameDTO:
    """Single audio frame emitted by the prototype exporter."""

    time: float
    effects: Tuple[SoundInstructionDTO, ...]
    music: Tuple[MusicInstructionDTO, ...]
    metadata: Mapping[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AudioFrameDTO":
        effects_payload = payload.get("effects", [])
        music_payload = payload.get("music", [])
        metadata_payload = payload.get("metadata", {})
        return cls(
            time=float(payload.get("time", 0.0)),
            effects=tuple(
                SoundInstructionDTO.from_dict(entry)
                for entry in effects_payload  # type: ignore[arg-type]
            ),
            music=tuple(
                MusicInstructionDTO.from_dict(entry)
                for entry in music_payload  # type: ignore[arg-type]
            ),
            metadata=dict(metadata_payload),
        )

    @classmethod
    def from_json(cls, payload: str) -> "AudioFrameDTO":
        data: Dict[str, Any] = json.loads(payload)
        return cls.from_dict(data)


@dataclass(frozen=True)
class AudioManifestDTO:
    """Routing table describing all audio assets and bindings."""

    effects: Dict[str, SoundClipDescriptor]
    music: Dict[str, MusicTrackDescriptor]
    event_effects: Dict[str, Tuple[str, ...]]
    event_music: Dict[str, Tuple[str, ...]]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AudioManifestDTO":
        effects_payload = payload.get("effects", {})
        music_payload = payload.get("music", {})
        event_effects_payload = payload.get("event_effects", {})
        event_music_payload = payload.get("event_music", {})

        if isinstance(effects_payload, Mapping):
            effect_entries = effects_payload.items()
        else:
            effect_entries = (
                (entry.get("id"), entry)
                for entry in effects_payload  # type: ignore[list-item]
                if isinstance(entry, Mapping)
            )
        effects = {
            str(effect_id): SoundClipDescriptor.from_dict(
                {"id": effect_id, **entry}
            )
            for effect_id, entry in effect_entries
            if effect_id is not None and isinstance(entry, Mapping)
        }

        if isinstance(music_payload, Mapping):
            music_entries = music_payload.items()
        else:
            music_entries = (
                (entry.get("id"), entry)
                for entry in music_payload  # type: ignore[list-item]
                if isinstance(entry, Mapping)
            )
        music = {
            str(track_id): MusicTrackDescriptor.from_dict({"id": track_id, **entry})
            for track_id, entry in music_entries
            if track_id is not None and isinstance(entry, Mapping)
        }
        event_effects = {
            str(event): tuple(str(item) for item in entries)
            for event, entries in event_effects_payload.items()
        }
        event_music = {
            str(event): tuple(str(item) for item in entries)
            for event, entries in event_music_payload.items()
        }
        return cls(
            effects=effects,
            music=music,
            event_effects=event_effects,
            event_music=event_music,
        )


@dataclass(frozen=True)
class ResolvedEffectInstruction:
    """Effect instruction paired with the resolved clip descriptor."""

    instruction: SoundInstructionDTO
    clip: Optional[SoundClipDescriptor]


@dataclass(frozen=True)
class ResolvedMusicInstruction:
    """Music instruction paired with the resolved track descriptor."""

    instruction: MusicInstructionDTO
    track: Optional[MusicTrackDescriptor]


@dataclass(frozen=True)
class AudioPlaybackFrame:
    """Result returned by :class:`AudioPlaybackHarness`."""

    frame: AudioFrameDTO
    effects: Tuple[ResolvedEffectInstruction, ...]
    music: Tuple[ResolvedMusicInstruction, ...]


# Backwards compatibility alias used by earlier clients/tests.
AppliedAudioFrame = AudioPlaybackFrame


class AudioPlaybackHarness:
    """Resolve audio frames against the manifest for runtime playback."""

    def __init__(self, manifest: AudioManifestDTO, *, logger: logging.Logger | None = None) -> None:
        self._manifest = manifest
        self._logger = logger or LOGGER

    @property
    def manifest(self) -> AudioManifestDTO:
        return self._manifest

    def route(self, frame: AudioFrameDTO) -> AudioPlaybackFrame:
        return AudioPlaybackFrame(
            frame=frame,
            effects=tuple(self._resolve_effect(instruction) for instruction in frame.effects),
            music=tuple(self._resolve_music(instruction) for instruction in frame.music),
        )

    def route_payload(self, payload: Mapping[str, Any]) -> AudioPlaybackFrame:
        return self.route(AudioFrameDTO.from_dict(payload))

    def route_json(self, payload: str) -> AudioPlaybackFrame:
        return self.route(AudioFrameDTO.from_json(payload))

    def _resolve_effect(self, instruction: SoundInstructionDTO) -> ResolvedEffectInstruction:
        clip = self._manifest.effects.get(instruction.clip.id)
        if clip is None:
            self._logger.warning(
                "Unknown sound clip %s (path=%s)",
                instruction.clip.id,
                instruction.clip.path,
            )
        return ResolvedEffectInstruction(instruction=instruction, clip=clip)

    def _resolve_music(self, instruction: MusicInstructionDTO) -> ResolvedMusicInstruction:
        track: Optional[MusicTrackDescriptor]
        if instruction.track is None:
            track = None
        else:
            track = self._manifest.music.get(instruction.track.id)
            if track is None:
                self._logger.warning(
                    "Unknown music track %s (path=%s)",
                    instruction.track.id,
                    instruction.track.path,
                )
        return ResolvedMusicInstruction(instruction=instruction, track=track)


@dataclass(frozen=True)
class EffectPlaybackEvent:
    """Mixer-ready effect payload used by the native runtime."""

    clip: SoundClipDescriptor
    volume: float
    pan: float


@dataclass(frozen=True)
class MusicPlaybackEvent:
    """Mixer-ready music payload used by the native runtime."""

    track: Optional[MusicTrackDescriptor]
    action: str
    volume: float


@dataclass(frozen=True)
class AudioMixerResult:
    """Result returned when the audio mixer applies a frame."""

    time: float
    effects: Tuple[EffectPlaybackEvent, ...]
    music: Tuple[MusicPlaybackEvent, ...]


class AudioMixer:
    """Apply audio frames and maintain currently playing music state."""

    def __init__(self, harness: AudioPlaybackHarness) -> None:
        self._harness = harness
        self._current_track: Optional[str] = None

    @property
    def current_track(self) -> Optional[str]:
        return self._current_track

    def apply(self, frame: AudioFrameDTO) -> AudioMixerResult:
        routed = self._harness.route(frame)

        effects: list[EffectPlaybackEvent] = []
        for entry in routed.effects:
            clip = entry.clip or entry.instruction.clip
            effective_volume = entry.instruction.volume * (clip.volume if clip is not None else 1.0)
            effects.append(
                EffectPlaybackEvent(
                    clip=clip if clip is not None else entry.instruction.clip,
                    volume=effective_volume,
                    pan=entry.instruction.pan,
                )
            )

        music_events: list[MusicPlaybackEvent] = []
        for entry in routed.music:
            instruction = entry.instruction
            track = entry.track or instruction.track

            if instruction.action == "stop":
                self._current_track = None
            elif instruction.track is not None and instruction.action in {"play", "refresh"}:
                if track is not None:
                    self._current_track = track.id
                else:
                    self._current_track = instruction.track.id

            base_volume = track.volume if track is not None else 1.0
            effective_volume = instruction.volume if instruction.volume is not None else base_volume
            music_events.append(
                MusicPlaybackEvent(
                    track=track,
                    action=instruction.action,
                    volume=effective_volume,
                )
            )

        return AudioMixerResult(
            time=frame.time,
            effects=tuple(effects),
            music=tuple(music_events),
        )

    def apply_payload(self, payload: Mapping[str, Any]) -> AudioMixerResult:
        return self.apply(AudioFrameDTO.from_dict(payload))


def _tuple_of_strings(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (str, bytes, bytearray)):
        return (str(value),)
    try:
        return tuple(str(entry) for entry in value)  # type: ignore[arg-type]
    except TypeError:
        return (str(value),)


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "AudioFrameDTO",
    "AudioManifestDTO",
    "AudioPlaybackFrame",
    "AudioPlaybackHarness",
    "AudioMixer",
    "AudioMixerResult",
    "AppliedAudioFrame",
    "MusicInstructionDTO",
    "MusicTrackDescriptor",
    "MusicPlaybackEvent",
    "ResolvedEffectInstruction",
    "ResolvedMusicInstruction",
    "SoundClipDescriptor",
    "SoundInstructionDTO",
    "EffectPlaybackEvent",
]

