"""Core systems that drive combat pacing and upgrade selection."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from . import config
from .content import build_wave_descriptor, draw_relic, final_boss_phases, pick_miniboss
from .localization import Translator, get_translator
from .entities import Encounter, GlyphFamily, Player, UpgradeCard


@dataclass(frozen=True)
class DifficultyProfile:
    name: str
    interval_multiplier: float
    density_multiplier: float


@dataclass(frozen=True)
class SpawnForecastEntry:
    """Lightweight description of an upcoming spawn window."""

    phase: int
    wave_index: int
    time: float
    interval: float
    max_density: int


DIFFICULTY_PROFILES = {
    "story": DifficultyProfile("story", interval_multiplier=1.15, density_multiplier=0.75),
    "standard": DifficultyProfile("standard", interval_multiplier=1.0, density_multiplier=1.0),
    "nightmare": DifficultyProfile("nightmare", interval_multiplier=0.85, density_multiplier=1.35),
}


class SpawnDirector:
    """Determines enemy spawn pacing based on phase and elapsed waves."""

    def __init__(self) -> None:
        self.wave_counters = {phase: 0 for phase in config.SPAWN_PHASES}
        self._interval_scale = 1.0
        self._density_scale = 1.0
        self._difficulty_interval_scale = 1.0
        self._difficulty_density_scale = 1.0
        self._event_interval_scale = 1.0
        self._event_density_scale = 1.0
        self._recompute_scales()

    def next_interval(self, phase: int) -> float:
        schedule = config.SPAWN_PHASES[phase]
        index = self.wave_counters[phase]
        self.wave_counters[phase] += 1
        interval = schedule.interval_for_wave(index) * self._interval_scale
        return max(0.5, interval)

    def max_density(self, phase: int) -> int:
        base = config.SPAWN_PHASES[phase].max_density
        scaled = int(round(base * self._density_scale))
        return max(1, scaled)

    def apply_difficulty_profile(self, profile: str) -> None:
        """Apply a named difficulty profile to the spawn pacing."""

        if profile not in DIFFICULTY_PROFILES:
            raise KeyError(f"unknown difficulty profile '{profile}'")
        settings = DIFFICULTY_PROFILES[profile]
        self._difficulty_interval_scale = max(0.25, settings.interval_multiplier)
        self._difficulty_density_scale = max(0.25, settings.density_multiplier)
        self._recompute_scales()

    def apply_event_modifiers(
        self,
        *,
        density_multiplier: float = 1.0,
        interval_multiplier: float | None = None,
    ) -> None:
        """Adjust spawn pacing in response to seasonal events."""

        if density_multiplier <= 0:
            raise ValueError("density_multiplier must be positive")
        if interval_multiplier is not None and interval_multiplier <= 0:
            raise ValueError("interval_multiplier must be positive")

        self._event_density_scale = max(0.25, density_multiplier)
        if interval_multiplier is None:
            self._event_interval_scale = 1.0 / self._event_density_scale
        else:
            self._event_interval_scale = max(0.25, interval_multiplier)
        self._recompute_scales()

    def forecast(
        self, phase: int, waves: int, *, start_time: float = 0.0
    ) -> Sequence[SpawnForecastEntry]:
        """Return a lookahead of upcoming spawn timings without mutating state."""

        if waves <= 0:
            return ()

        schedule = config.SPAWN_PHASES[phase]
        start_index = self.wave_counters[phase]
        entries: List[SpawnForecastEntry] = []
        current_time = start_time
        for offset in range(waves):
            wave_index = start_index + offset
            interval = max(0.5, schedule.interval_for_wave(wave_index) * self._interval_scale)
            spawn_time = current_time + interval
            current_time = spawn_time
            max_density = int(round(schedule.max_density * self._density_scale))
            entries.append(
                SpawnForecastEntry(
                    phase=phase,
                    wave_index=wave_index,
                    time=spawn_time,
                    interval=interval,
                    max_density=max(1, max_density),
                )
            )

        return tuple(entries)

    def _recompute_scales(self) -> None:
        self._interval_scale = self._difficulty_interval_scale * self._event_interval_scale
        self._density_scale = self._difficulty_density_scale * self._event_density_scale


class UpgradeDeck:
    """Handles randomization of upgrades for level-up rewards."""

    def __init__(self, available_cards: Iterable[UpgradeCard]) -> None:
        self._pool = list(available_cards)
        if not self._pool:
            raise ValueError("upgrade deck requires at least one card")

    def draw_options(self) -> List[UpgradeCard]:
        count = min(config.MAX_UPGRADE_OPTIONS, len(self._pool))
        return random.sample(self._pool, count)


def resolve_experience_gain(
    player: Player, amount: int, translator: Translator | None = None
) -> List[str]:
    """Apply experience and return milestone notifications."""

    if amount < 0:
        raise ValueError("amount must be non-negative")

    notifications: List[str] = []
    player.experience += amount

    translator = translator or get_translator()

    while player.experience >= config.LEVEL_CURVE.xp_for_level(player.level + 1):
        player.level += 1
        notifications.append(translator.translate("systems.level_up", level=player.level))
        for family in player.complete_glyph_sets():
            notifications.append(
                translator.translate("systems.ultimate_unlocked", family=family.value)
            )

    return notifications


def grant_glyph_set(player: Player, family: GlyphFamily) -> List[GlyphFamily]:
    """Utility method to increment glyphs to a complete set and return completions."""

    for _ in range(config.GLYPH_SET_SIZE):
        player.add_glyph(family)
    return player.complete_glyph_sets()


class EncounterDirector:
    """Generates encounters (waves and miniboss fights) for the run."""

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self._rng = rng or random.Random()
        self._wave_indices = {phase: 0 for phase in config.SPAWN_PHASES}

    def next_encounter(self, phase: int) -> Encounter:
        wave_index = self._wave_indices[phase]
        self._wave_indices[phase] += 1

        if (wave_index + 1) % 5 == 0:
            miniboss = pick_miniboss(phase, self._rng)
            relic = draw_relic(self._rng)
            return Encounter(kind="miniboss", miniboss=miniboss, relic_reward=relic)

        wave = build_wave_descriptor(phase, wave_index, self._rng)
        return Encounter(kind="wave", wave=wave)

    def wave_index(self, phase: int) -> int:
        """Expose the next wave index for inspection (useful for tests)."""

        return self._wave_indices[phase]

    def final_encounter(self) -> Encounter:
        """Return the climactic final boss encounter."""

        phases = final_boss_phases()
        return Encounter(kind="final_boss", boss_phases=phases)

