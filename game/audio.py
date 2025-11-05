"""Audio abstraction bridging gameplay events to a sound pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
)


@dataclass(frozen=True)
class SoundClip:
    """Definition for a short effect that can be played on demand."""

    id: str
    path: str
    volume: float = 1.0


@dataclass(frozen=True)
class MusicTrack:
    """Looping or one-shot music asset."""

    id: str
    path: str
    volume: float = 1.0
    loop: bool = True


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
                effect_id: {"path": clip.path, "volume": clip.volume}
                for effect_id, clip in self.effects.items()
            },
            "music": {
                track_id: {
                    "path": track.path,
                    "volume": track.volume,
                    "loop": track.loop,
                }
                for track_id, track in self.music.items()
            },
            "event_effects": {
                event: list(entries) for event, entries in self.event_effects.items()
            },
            "event_music": {
                event: list(entries) for event, entries in self.event_music.items()
            },
        }


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
        for effect_id, definition in DEFAULT_AUDIO_CUE_TABLE["effects"].items():
            self.register_effect(
                SoundClip(
                    id=effect_id,
                    path=definition["path"],
                    volume=definition["volume"],
                )
            )
        for track_id, definition in DEFAULT_AUDIO_CUE_TABLE["music"].items():
            self.register_music(
                MusicTrack(
                    id=track_id,
                    path=definition["path"],
                    volume=definition["volume"],
                    loop=definition["loop"],
                )
            )
        for event, routes in DEFAULT_AUDIO_CUE_TABLE["event_effects"].items():
            self.bind_effect(event, *routes)
        for event, routes in DEFAULT_AUDIO_CUE_TABLE["event_music"].items():
            self.bind_music(event, *routes)

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


class EffectDefinition(TypedDict):
    """Schema for an effect entry in the default cue table."""

    path: str
    volume: float


class MusicDefinition(TypedDict):
    """Schema for a music entry in the default cue table."""

    path: str
    volume: float
    loop: bool


class AudioCueTable(TypedDict):
    """Mapping describing the built-in audio cues and routing."""

    effects: Dict[str, EffectDefinition]
    music: Dict[str, MusicDefinition]
    event_effects: Dict[str, Tuple[str, ...]]
    event_music: Dict[str, Tuple[str, ...]]


DEFAULT_AUDIO_CUE_TABLE: AudioCueTable = {
    "effects": {
        "effects/ui.confirm": {"path": "audio/ui_confirm.ogg", "volume": 0.75},
        "effects/ui.prompt": {"path": "audio/ui_prompt.ogg", "volume": 0.6},
        "effects/combat.hit": {"path": "audio/combat_hit.ogg", "volume": 0.8},
        "effects/combat.enemy_down": {
            "path": "audio/enemy_down.ogg",
            "volume": 0.9,
        },
        "effects/combat.weapon": {
            "path": "audio/weapon_fire.ogg",
            "volume": 0.65,
        },
        "effects/combat.ultimate": {"path": "audio/ultimate.ogg", "volume": 1.0},
        "effects/player.damage": {
            "path": "audio/player_damage.ogg",
            "volume": 0.85,
        },
        "effects/player.dash": {"path": "audio/player_dash.ogg", "volume": 0.8},
        "effects/run.victory": {
            "path": "audio/victory_sting.ogg",
            "volume": 1.0,
        },
        "effects/run.defeat": {"path": "audio/defeat_sting.ogg", "volume": 1.0},
        "effects/enemy.spawn": {"path": "audio/enemy_spawn.ogg", "volume": 0.55},
        "effects/environment.hazard": {
            "path": "audio/environment_hazard.ogg",
            "volume": 0.8,
        },
        "effects/environment.salvage": {
            "path": "audio/environment_salvage.ogg",
            "volume": 0.65,
        },
        "effects/environment.weather_change": {
            "path": "audio/environment_weather_change.ogg",
            "volume": 0.7,
        },
        "effects/environment.weather_clear": {
            "path": "audio/environment_weather_clear.ogg",
            "volume": 0.6,
        },
    },
    "music": {
        "music.dusk_theme": {
            "path": "audio/music_dusk.ogg",
            "volume": 0.7,
            "loop": True,
        },
        "music.boss_theme": {
            "path": "audio/music_boss.ogg",
            "volume": 0.8,
            "loop": True,
        },
    },
    "event_effects": {
        "ui.upgrade_selected": ("effects/ui.confirm",),
        "ui.level_up": ("effects/ui.prompt",),
        "ui.upgrade_presented": ("effects/ui.prompt",),
        "combat.weapon_fire": ("effects/combat.weapon",),
        "combat.enemy_down": ("effects/combat.enemy_down",),
        "combat.enemy_spawn": ("effects/enemy.spawn",),
        "combat.hit": ("effects/combat.hit",),
        "player.damage": ("effects/player.damage",),
        "player.dash": ("effects/player.dash",),
        "combat.ultimate": ("effects/combat.ultimate",),
        "run.victory": ("effects/run.victory",),
        "run.defeat": ("effects/run.defeat",),
        "run.miniboss_warning": ("effects/ui.prompt",),
        "run.relic_acquired": ("effects/ui.confirm",),
        "run.final_boss_warning": ("effects/ui.prompt",),
        "run.final_boss_defeated": ("effects/run.victory",),
        "accessibility.health.low": ("effects/ui.prompt",),
        "accessibility.upgrade.prompt": ("effects/ui.confirm",),
        "environment.hazard": ("effects/environment.hazard",),
        "environment.salvage": ("effects/environment.salvage",),
        "environment.weather.change": (
            "effects/environment.weather_change",
        ),
        "environment.weather.clear": (
            "effects/environment.weather_clear",
        ),
    },
    "event_music": {
        "music.start": ("music.dusk_theme",),
        "music.boss": ("music.boss_theme",),
    },
}


def default_audio_cue_table() -> AudioCueTable:
    """Return a deep copy of the default cue table for external consumers."""

    return {
        "effects": {
            effect_id: dict(definition)
            for effect_id, definition in DEFAULT_AUDIO_CUE_TABLE["effects"].items()
        },
        "music": {
            track_id: dict(definition)
            for track_id, definition in DEFAULT_AUDIO_CUE_TABLE["music"].items()
        },
        "event_effects": {
            event: tuple(routes)
            for event, routes in DEFAULT_AUDIO_CUE_TABLE["event_effects"].items()
        },
        "event_music": {
            event: tuple(routes)
            for event, routes in DEFAULT_AUDIO_CUE_TABLE["event_music"].items()
        },
    }



__all__ = [
    "AudioEngine",
    "AudioManifest",
    "AudioFrame",
    "MusicInstruction",
    "MusicTrack",
    "SoundClip",
    "SoundInstruction",
    "EffectDefinition",
    "MusicDefinition",
    "AudioCueTable",
    "DEFAULT_AUDIO_CUE_TABLE",
    "default_audio_cue_table",
]
