"""Audio abstraction bridging gameplay events to a sound pipeline."""

from __future__ import annotations

import json
import math
import wave
from array import array
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SoundClip:
    """Definition for a short effect that can be played on demand."""

    id: str
    path: str
    volume: float = 1.0
    description: str = ""
    tags: Tuple[str, ...] = ()
    length_seconds: Optional[float] = None


@dataclass(frozen=True)
class MusicTrack:
    """Looping or one-shot music asset."""

    id: str
    path: str
    volume: float = 1.0
    loop: bool = True
    description: str = ""
    tags: Tuple[str, ...] = ()
    length_seconds: Optional[float] = None
    tempo_bpm: Optional[float] = None


@dataclass(frozen=True)
class SoundInstruction:
    """Instruction for a playback engine to play an effect."""

    clip: SoundClip
    volume: float
    pan: float = 0.0


@dataclass(frozen=True)
class MusicInstruction:
    """Instruction describing how to update background music."""

    track: Optional[MusicTrack]
    action: str
    volume: Optional[float] = None


@dataclass(frozen=True)
class AudioFrame:
    """Audio commands generated for a particular frame."""

    time: float
    effects: Sequence[SoundInstruction]
    music: Sequence[MusicInstruction] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AudioManifest:
    """Serializable snapshot of the audio routing table."""

    effects: Mapping[str, SoundClip]
    music: Mapping[str, MusicTrack]
    event_effects: Mapping[str, Sequence[str]]
    event_music: Mapping[str, Sequence[str]]

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation of the manifest."""

        return {
            "effects": {
                effect_id: _ManifestEffectEntry(
                    path=clip.path,
                    volume=clip.volume,
                    metadata={
                        "description": clip.description,
                        "tags": list(clip.tags),
                        "length_seconds": clip.length_seconds,
                    },
                )
                for effect_id, clip in self.effects.items()
            },
            "music": {
                track_id: _ManifestMusicEntry(
                    path=track.path,
                    volume=track.volume,
                    loop=track.loop,
                    metadata={
                        "description": track.description,
                        "tags": list(track.tags),
                        "length_seconds": track.length_seconds,
                        "tempo_bpm": track.tempo_bpm,
                    },
                )
                for track_id, track in self.music.items()
            },
            "event_effects": {
                event: list(entries) for event, entries in self.event_effects.items()
            },
            "event_music": {
                event: list(entries) for event, entries in self.event_music.items()
            },
        }


class _ManifestBaseEntry(dict):
    """Dictionary-like view that exposes metadata without affecting equality."""

    def __init__(self, base: Mapping[str, Any], metadata: Mapping[str, Any]) -> None:
        filtered = {
            key: value for key, value in metadata.items() if value not in (None, [], "", ())
        }
        super().__init__(base)
        self._metadata = filtered

    def __getitem__(self, key: str) -> Any:  # type: ignore[override]
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        return self._metadata[key]

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        if dict.__contains__(self, key):
            return dict.get(self, key, default)
        return self._metadata.get(key, default)

    def __contains__(self, key: object) -> bool:  # type: ignore[override]
        return dict.__contains__(self, key) or key in self._metadata

    def keys(self):  # type: ignore[override]
        return list(dict.keys(self)) + [key for key in self._metadata if key not in self]

    def items(self):  # type: ignore[override]
        for item in dict.items(self):
            yield item
        for item in self._metadata.items():
            if item[0] not in self:
                yield item

    def values(self):  # type: ignore[override]
        for value in dict.values(self):
            yield value
        for key, value in self._metadata.items():
            if key not in self:
                yield value


class _ManifestEffectEntry(_ManifestBaseEntry):
    def __init__(self, *, path: str, volume: float, metadata: Mapping[str, Any]) -> None:
        super().__init__({"path": path, "volume": volume}, metadata)


class _ManifestMusicEntry(_ManifestBaseEntry):
    def __init__(self, *, path: str, volume: float, loop: bool, metadata: Mapping[str, Any]) -> None:
        base = {"path": path, "volume": volume, "loop": loop}
        super().__init__(base, metadata)


class AudioEngine:
    """Lightweight router that maps gameplay events to audio instructions."""

    def __init__(self) -> None:
        self._effects: Dict[str, SoundClip] = {}
        self._music: Dict[str, MusicTrack] = {}
        self._event_effects: MutableMapping[str, List[str]] = {}
        self._event_music: MutableMapping[str, List[str]] = {}
        self._current_track: Optional[str] = None
        self._placeholders_registered = False

    @property
    def asset_manifest_path(self) -> Path:
        """Return the path to the checked-in audio manifest."""

        return Path(__file__).resolve().parent.parent / "assets" / "audio" / "manifest.json"

    @property
    def current_track(self) -> Optional[str]:
        return self._current_track

    def register_effect(self, clip: SoundClip) -> None:
        self._effects[clip.id] = clip

    def register_music(self, track: MusicTrack) -> None:
        self._music[track.id] = track

    def bind_effect(self, event: str, *effect_ids: str) -> None:
        slots = self._event_effects.setdefault(event, [])
        for effect in effect_ids:
            if effect not in slots:
                slots.append(effect)

    def bind_music(self, event: str, *track_ids: str) -> None:
        slots = self._event_music.setdefault(event, [])
        for track in track_ids:
            if track not in slots:
                slots.append(track)

    def ensure_placeholders(self) -> None:
        """Register placeholder clips if none exist yet."""

        if self._placeholders_registered:
            return

        self._placeholders_registered = True
        payload = _load_audio_asset_payload(self.asset_manifest_path)

        if payload is None:
            _register_default_audio_placeholders(self)
            return

        materialise_audio_manifest_assets(
            payload, asset_root=self.asset_manifest_path.parent.parent
        )

        for entry in payload.get("effects", []):
            clip = SoundClip(
                id=str(entry.get("id")),
                path=str(entry.get("path")),
                volume=float(entry.get("volume", 1.0)),
                description=str(entry.get("description", "")),
                tags=_as_tuple(entry.get("tags", ())),
                length_seconds=_optional_float(entry.get("length_seconds")),
            )
            self.register_effect(clip)

        for entry in payload.get("music", []):
            track = MusicTrack(
                id=str(entry.get("id")),
                path=str(entry.get("path")),
                volume=float(entry.get("volume", 1.0)),
                loop=bool(entry.get("loop", True)),
                description=str(entry.get("description", "")),
                tags=_as_tuple(entry.get("tags", ())),
                length_seconds=_optional_float(entry.get("length_seconds")),
                tempo_bpm=_optional_float(entry.get("tempo_bpm")),
            )
            self.register_music(track)

        for event, effect_ids in payload.get("event_effects", {}).items():
            self.bind_effect(str(event), *(_as_tuple(effect_ids)))

        for event, music_ids in payload.get("event_music", {}).items():
            self.bind_music(str(event), *(_as_tuple(music_ids)))

    def build_frame(
        self,
        events: Iterable[str],
        *,
        time: float,
    ) -> AudioFrame:
        """Convert gameplay events into audio instructions."""

        self.ensure_placeholders()
        effects: List[SoundInstruction] = []
        music: List[MusicInstruction] = []

        for event in events:
            if event in self._event_effects:
                for effect_id in self._event_effects[event]:
                    clip = self._effects.get(effect_id)
                    if clip:
                        effects.append(SoundInstruction(clip=clip, volume=clip.volume))
            if event in self._event_music:
                for track_id in self._event_music[event]:
                    track = self._music.get(track_id)
                    if not track:
                        continue
                    if track_id != self._current_track:
                        self._current_track = track_id
                        music.append(MusicInstruction(track=track, action="play", volume=track.volume))
                    else:
                        music.append(MusicInstruction(track=track, action="refresh"))

        return AudioFrame(time=time, effects=tuple(effects), music=tuple(music))

    def build_manifest(self) -> AudioManifest:
        """Return an :class:`AudioManifest` describing registered assets and routes."""

        self.ensure_placeholders()
        return AudioManifest(
            effects=dict(self._effects),
            music=dict(self._music),
            event_effects={event: tuple(effects) for event, effects in self._event_effects.items()},
            event_music={event: tuple(tracks) for event, tracks in self._event_music.items()},
        )


def _as_tuple(value: object) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (str, bytes)):
        return (str(value),)
    try:
        return tuple(str(entry) for entry in value)  # type: ignore[arg-type]
    except TypeError:
        return (str(value),)


def _optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_audio_asset_payload(path: Path) -> Optional[dict]:
    try:
        raw = path.read_text()
    except FileNotFoundError:  # pragma: no cover - defensive for downstream repos
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:  # pragma: no cover - invalid manifest should fall back
        return None


def _register_default_audio_placeholders(engine: AudioEngine) -> None:
    engine.register_effect(
        SoundClip(id="effects/ui.confirm", path="audio/ui_confirm.wav", volume=0.75)
    )
    engine.register_effect(
        SoundClip(id="effects/ui.prompt", path="audio/ui_prompt.wav", volume=0.6)
    )
    engine.register_effect(
        SoundClip(id="effects/combat.hit", path="audio/combat_hit.wav", volume=0.8)
    )
    engine.register_effect(
        SoundClip(id="effects/combat.enemy_down", path="audio/enemy_down.wav", volume=0.9)
    )
    engine.register_effect(
        SoundClip(id="effects/combat.weapon", path="audio/weapon_fire.wav", volume=0.65)
    )
    engine.register_effect(
        SoundClip(id="effects/combat.ultimate", path="audio/ultimate.wav", volume=1.0)
    )
    engine.register_effect(
        SoundClip(id="effects/player.damage", path="audio/player_damage.wav", volume=0.85)
    )
    engine.register_effect(
        SoundClip(id="effects/player.dash", path="audio/player_dash.wav", volume=0.8)
    )
    engine.register_effect(
        SoundClip(id="effects/run.victory", path="audio/victory_sting.wav", volume=1.0)
    )
    engine.register_effect(
        SoundClip(id="effects/run.defeat", path="audio/defeat_sting.wav", volume=1.0)
    )
    engine.register_effect(
        SoundClip(id="effects/enemy.spawn", path="audio/enemy_spawn.wav", volume=0.55)
    )
    engine.register_effect(
        SoundClip(id="effects/environment.hazard", path="audio/environment_hazard.wav", volume=0.8)
    )
    engine.register_effect(
        SoundClip(id="effects/environment.salvage", path="audio/environment_salvage.wav", volume=0.65)
    )
    engine.register_effect(
        SoundClip(
            id="effects/environment.weather_change",
            path="audio/environment_weather_change.wav",
            volume=0.7,
        )
    )
    engine.register_effect(
        SoundClip(
            id="effects/environment.weather_clear",
            path="audio/environment_weather_clear.wav",
            volume=0.6,
        )
    )
    engine.register_music(
        MusicTrack(id="music.dusk_theme", path="audio/music_dusk.wav", volume=0.7, loop=True)
    )
    engine.register_music(
        MusicTrack(id="music.boss_theme", path="audio/music_boss.wav", volume=0.8, loop=True)
    )
    engine.bind_effect("ui.upgrade_selected", "effects/ui.confirm")
    engine.bind_effect("ui.level_up", "effects/ui.prompt")
    engine.bind_effect("ui.upgrade_presented", "effects/ui.prompt")
    engine.bind_effect("combat.weapon_fire", "effects/combat.weapon")
    engine.bind_effect("combat.enemy_down", "effects/combat.enemy_down")
    engine.bind_effect("combat.enemy_spawn", "effects/enemy.spawn")
    engine.bind_effect("player.damage", "effects/player.damage")
    engine.bind_effect("player.dash", "effects/player.dash")
    engine.bind_effect("combat.ultimate", "effects/combat.ultimate")
    engine.bind_effect("run.victory", "effects/run.victory")
    engine.bind_effect("run.defeat", "effects/run.defeat")
    engine.bind_effect("run.miniboss_warning", "effects/ui.prompt")
    engine.bind_effect("run.relic_acquired", "effects/ui.confirm")
    engine.bind_effect("run.final_boss_warning", "effects/ui.prompt")
    engine.bind_effect("run.final_boss_defeated", "effects/run.victory")
    engine.bind_effect("accessibility.health.low", "effects/ui.prompt")
    engine.bind_effect("accessibility.upgrade.prompt", "effects/ui.confirm")
    engine.bind_effect("environment.hazard", "effects/environment.hazard")
    engine.bind_effect("environment.salvage", "effects/environment.salvage")
    engine.bind_effect("environment.weather.change", "effects/environment.weather_change")
    engine.bind_effect("environment.weather.clear", "effects/environment.weather_clear")
    engine.bind_music("music.start", "music.dusk_theme")
    engine.bind_music("music.boss", "music.boss_theme")


def materialise_audio_manifest_assets(
    payload: Mapping[str, Any], *, asset_root: Path
) -> None:
    """Generate placeholder audio files declared in the manifest if missing."""

    for section in ("effects", "music"):
        for entry in payload.get(section, []):
            _ensure_placeholder_wave(asset_root, entry)


_DEFAULT_SAMPLE_RATE = 22_050


def _ensure_placeholder_wave(asset_root: Path, entry: Mapping[str, Any]) -> None:
    relative = entry.get("path")
    if not relative:
        return
    target = asset_root / str(relative)
    if target.exists():
        return

    synthesis = entry.get("synthesis")
    if not isinstance(synthesis, Mapping):
        raise RuntimeError(
            f"No synthesis recipe provided for placeholder audio asset {entry.get('id')}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    samples, sample_rate = _synthesise_waveform(
        synthesis,
        fallback_duration=float(entry.get("length_seconds", 0.5) or 0.5),
    )
    _write_wave_file(target, samples, sample_rate)


def _synthesise_waveform(
    synthesis: Mapping[str, Any], *, fallback_duration: float
) -> Tuple[array, int]:
    sample_rate = int(synthesis.get("sample_rate", _DEFAULT_SAMPLE_RATE))
    duration = float(synthesis.get("duration_seconds", fallback_duration))
    duration = duration if duration > 0 else fallback_duration
    total_samples = max(1, int(sample_rate * duration))
    amplitude = float(synthesis.get("amplitude", 0.3))
    kind = str(synthesis.get("type", "tone"))

    generators = {
        "tone": _generate_tone_samples,
        "chord": _generate_chord_samples,
        "sweep": _generate_sweep_samples,
        "noise": _generate_noise_samples,
    }

    try:
        builder = generators[kind]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Unsupported synthesis type: {kind}") from exc

    buffer = builder(synthesis, total_samples, sample_rate)
    _apply_envelope(buffer, synthesis.get("envelope"), sample_rate)

    max_amplitude = max(1.0, abs(max(buffer, default=0.0)), abs(min(buffer, default=0.0)))
    scale = max(0.0, min(amplitude, 1.0)) / max_amplitude if max_amplitude else 0.0
    samples = array(
        "h",
        (
            int(max(-1.0, min(1.0, value * scale)) * 32767)
            for value in buffer
        ),
    )
    return samples, sample_rate


def _generate_tone_samples(
    synthesis: Mapping[str, Any], total_samples: int, sample_rate: int
) -> List[float]:
    frequency = float(synthesis.get("frequency", 440.0))
    partials = synthesis.get("partials") or [1.0]
    multipliers = [float(part) for part in partials]
    phases = [0.0 for _ in multipliers]
    increments = [2 * math.pi * frequency * mult / sample_rate for mult in multipliers]

    buffer: List[float] = [0.0] * total_samples
    for index in range(total_samples):
        sample = 0.0
        for slot, step in enumerate(increments):
            phases[slot] += step
            sample += math.sin(phases[slot])
        buffer[index] = sample / max(1, len(increments))
    return buffer


def _generate_chord_samples(
    synthesis: Mapping[str, Any], total_samples: int, sample_rate: int
) -> List[float]:
    frequencies = synthesis.get("frequencies") or [440.0]
    freqs = [float(freq) for freq in frequencies]
    phases = [0.0 for _ in freqs]
    increments = [2 * math.pi * freq / sample_rate for freq in freqs]

    buffer: List[float] = [0.0] * total_samples
    for index in range(total_samples):
        sample = 0.0
        for slot, step in enumerate(increments):
            phases[slot] += step
            sample += math.sin(phases[slot])
        buffer[index] = sample / max(1, len(increments))
    return buffer


def _generate_sweep_samples(
    synthesis: Mapping[str, Any], total_samples: int, sample_rate: int
) -> List[float]:
    start_frequency = float(synthesis.get("start_frequency", 220.0))
    end_frequency = float(synthesis.get("end_frequency", start_frequency))
    phase = 0.0
    buffer: List[float] = [0.0] * total_samples
    for index in range(total_samples):
        progress = index / max(1, total_samples - 1)
        frequency = start_frequency + (end_frequency - start_frequency) * progress
        phase += 2 * math.pi * frequency / sample_rate
        buffer[index] = math.sin(phase)
    return buffer


def _generate_noise_samples(
    synthesis: Mapping[str, Any], total_samples: int, sample_rate: int
) -> List[float]:
    seed = int(synthesis.get("seed", 1337)) & 0x7FFFFFFF
    state = seed or 1
    lowpass = float(synthesis.get("lowpass", 0.0))
    alpha: Optional[float]
    if lowpass > 0:
        cutoff = min(lowpass, sample_rate / 2.0)
        rc = 1.0 / (2 * math.pi * cutoff)
        dt = 1.0 / sample_rate
        alpha = dt / (rc + dt)
    else:
        alpha = None
    previous = 0.0
    buffer: List[float] = [0.0] * total_samples
    for index in range(total_samples):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        value = ((state / 0x7FFFFFFF) * 2.0) - 1.0
        if alpha is not None:
            previous = previous + alpha * (value - previous)
            value = previous
        buffer[index] = value
    return buffer


def _apply_envelope(
    buffer: List[float], envelope: object, sample_rate: int
) -> None:
    if not isinstance(envelope, Mapping):
        return

    attack = max(0.0, float(envelope.get("attack", 0.0)))
    decay = max(0.0, float(envelope.get("decay", 0.0)))
    sustain_level = float(envelope.get("sustain", envelope.get("sustain_level", 1.0)))
    sustain_level = max(0.0, min(sustain_level, 1.0))
    release = max(0.0, float(envelope.get("release", 0.0)))

    total = len(buffer)
    attack_samples = min(total, int(attack * sample_rate))
    decay_samples = min(max(0, total - attack_samples), int(decay * sample_rate))
    release_samples = min(total, int(release * sample_rate))
    sustain_samples = total - attack_samples - decay_samples - release_samples
    if sustain_samples < 0:
        release_samples = max(0, release_samples + sustain_samples)
        sustain_samples = 0

    envelope_curve = [0.0] * total
    index = 0

    for offset in range(attack_samples):
        envelope_curve[index] = (offset + 1) / max(1, attack_samples)
        index += 1

    last_level = envelope_curve[index - 1] if index else 1.0
    for offset in range(decay_samples):
        level = 1.0 - (1.0 - sustain_level) * (offset + 1) / max(1, decay_samples)
        envelope_curve[index] = level
        last_level = level
        index += 1

    for _ in range(sustain_samples):
        envelope_curve[index] = sustain_level
        last_level = sustain_level
        index += 1

    for offset in range(release_samples):
        envelope_curve[index] = max(0.0, last_level * (1.0 - (offset + 1) / max(1, release_samples)))
        index += 1

    while index < total:
        envelope_curve[index] = 0.0
        index += 1

    for idx, level in enumerate(envelope_curve):
        buffer[idx] *= level


def _write_wave_file(path: Path, samples: array, sample_rate: int) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(samples.tobytes())


def _build_default_audio_cue_table() -> Dict[str, Any]:
    engine = AudioEngine()
    engine.ensure_placeholders()
    manifest = engine.build_manifest().to_dict()

    effects = {key: dict(entry) for key, entry in manifest["effects"].items()}
    music = {key: dict(entry) for key, entry in manifest["music"].items()}
    event_effects = {event: tuple(routes) for event, routes in manifest["event_effects"].items()}
    event_music = {event: tuple(routes) for event, routes in manifest["event_music"].items()}

    return {
        "effects": effects,
        "music": music,
        "event_effects": event_effects,
        "event_music": event_music,
    }


DEFAULT_AUDIO_CUE_TABLE = _build_default_audio_cue_table()


def default_audio_cue_table() -> Dict[str, Any]:
    """Return a deep copy of :data:`DEFAULT_AUDIO_CUE_TABLE`."""

    return json.loads(json.dumps(DEFAULT_AUDIO_CUE_TABLE))


__all__ = [
    "AudioEngine",
    "AudioManifest",
    "AudioFrame",
    "MusicInstruction",
    "MusicTrack",
    "SoundClip",
    "SoundInstruction",
    "DEFAULT_AUDIO_CUE_TABLE",
    "default_audio_cue_table",
    "materialise_audio_manifest_assets",
]
