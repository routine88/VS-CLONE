"""Core systems that drive combat pacing and upgrade selection."""

from __future__ import annotations

import random
from typing import Iterable, List, Optional

from . import config
from .content import build_wave_descriptor, draw_relic, final_boss_phases, pick_miniboss
from .entities import Encounter, GlyphFamily, Player, UpgradeCard


class SpawnDirector:
    """Determines enemy spawn pacing based on phase and elapsed waves."""

    def __init__(self) -> None:
        self.wave_counters = {phase: 0 for phase in config.SPAWN_PHASES}

    def next_interval(self, phase: int) -> float:
        schedule = config.SPAWN_PHASES[phase]
        index = self.wave_counters[phase]
        self.wave_counters[phase] += 1
        return schedule.interval_for_wave(index)

    def max_density(self, phase: int) -> int:
        return config.SPAWN_PHASES[phase].max_density


class UpgradeDeck:
    """Handles randomization of upgrades for level-up rewards."""

    def __init__(self, available_cards: Iterable[UpgradeCard]) -> None:
        self._pool = list(available_cards)
        if not self._pool:
            raise ValueError("upgrade deck requires at least one card")

    def draw_options(self) -> List[UpgradeCard]:
        count = min(config.MAX_UPGRADE_OPTIONS, len(self._pool))
        return random.sample(self._pool, count)


def resolve_experience_gain(player: Player, amount: int) -> List[str]:
    """Apply experience and return milestone notifications."""

    if amount < 0:
        raise ValueError("amount must be non-negative")

    notifications: List[str] = []
    player.experience += amount

    while player.experience >= config.LEVEL_CURVE.xp_for_level(player.level + 1):
        player.level += 1
        notifications.append(f"Level up! Reached level {player.level}.")
        for family in player.complete_glyph_sets():
            notifications.append(f"Ultimate unlocked for {family.value} glyphs!")

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

