"""Audio abstraction bridging gameplay events to a sound pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence


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
        self.register_effect(
            SoundClip(id="effects/ui.confirm", path="audio/ui_confirm.ogg", volume=0.75)
        )
        self.register_effect(
            SoundClip(id="effects/ui.prompt", path="audio/ui_prompt.ogg", volume=0.6)
        )
        self.register_effect(
            SoundClip(id="effects/combat.hit", path="audio/combat_hit.ogg", volume=0.8)
        )
        self.register_effect(
            SoundClip(id="effects/combat.enemy_down", path="audio/enemy_down.ogg", volume=0.9)
        )
        self.register_effect(
            SoundClip(id="effects/combat.weapon", path="audio/weapon_fire.ogg", volume=0.65)
        )
        self.register_effect(
            SoundClip(id="effects/combat.ultimate", path="audio/ultimate.ogg", volume=1.0)
        )
        self.register_effect(
            SoundClip(id="effects/player.damage", path="audio/player_damage.ogg", volume=0.85)
        )
        self.register_effect(
            SoundClip(id="effects/run.victory", path="audio/victory_sting.ogg", volume=1.0)
        )
        self.register_effect(
            SoundClip(id="effects/run.defeat", path="audio/defeat_sting.ogg", volume=1.0)
        )
        self.register_effect(
            SoundClip(id="effects/enemy.spawn", path="audio/enemy_spawn.ogg", volume=0.55)
        )
        self.register_music(
            MusicTrack(id="music.dusk_theme", path="audio/music_dusk.ogg", volume=0.7, loop=True)
        )
        self.register_music(
            MusicTrack(id="music.boss_theme", path="audio/music_boss.ogg", volume=0.8, loop=True)
        )
        self.bind_effect(
            "ui.upgrade_selected",
            "effects/ui.confirm",
        )
        self.bind_effect(
            "ui.level_up",
            "effects/ui.prompt",
        )
        self.bind_effect(
            "ui.upgrade_presented",
            "effects/ui.prompt",
        )
        self.bind_effect(
            "combat.weapon_fire",
            "effects/combat.weapon",
        )
        self.bind_effect(
            "combat.enemy_down",
            "effects/combat.enemy_down",
        )
        self.bind_effect(
            "combat.enemy_spawn",
            "effects/enemy.spawn",
        )
        self.bind_effect(
            "player.damage",
            "effects/player.damage",
        )
        self.bind_effect(
            "combat.ultimate",
            "effects/combat.ultimate",
        )
        self.bind_effect(
            "run.victory",
            "effects/run.victory",
        )
        self.bind_effect(
            "run.defeat",
            "effects/run.defeat",
        )
        self.bind_music("music.start", "music.dusk_theme")
        self.bind_music("music.boss", "music.boss_theme")

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


__all__ = [
    "AudioEngine",
    "AudioFrame",
    "MusicInstruction",
    "MusicTrack",
    "SoundClip",
    "SoundInstruction",
]
