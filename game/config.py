"""Gameplay tuning constants used by the prototype logic layer."""

from __future__ import annotations

from dataclasses import dataclass

import random


@dataclass(frozen=True)
class LevelCurve:
    """Represents XP thresholds required to reach each level."""

    base_xp: int = 30
    xp_growth: float = 1.45

    def xp_for_level(self, level: int) -> int:
        """Return the XP needed to reach *level* from level 1.

        The curve follows an exponential growth with soft rounding to make
        thresholds feel readable when surfaced in UI copy.
        """

        if level < 1:
            raise ValueError("level must be positive")
        total = 0
        for step in range(1, level):
            total += int(self.base_xp * (self.xp_growth ** (step - 1)))
        return total


@dataclass(frozen=True)
class SpawnSchedule:
    """Encapsulates enemy spawn parameters for a particular phase."""

    base_interval: float
    interval_decay: float
    max_density: int

    def interval_for_wave(self, wave_index: int) -> float:
        """Compute spawn interval for a given wave index."""

        interval = self.base_interval * (self.interval_decay ** wave_index)
        return max(interval, self.base_interval / 4)


@dataclass(frozen=True)
class HazardSchedule:
    """Encapsulates timing and scaling for environmental hazards."""

    base_interval: float
    interval_variance: float
    damage_scale: float

    def roll_interval(self, rng: random.Random) -> float:
        """Return the next interval before a hazard triggers."""

        if self.interval_variance <= 0:
            return self.base_interval
        lower = max(5.0, self.base_interval - self.interval_variance)
        upper = self.base_interval + self.interval_variance
        return rng.uniform(lower, upper)

    def scale_damage(self, base_damage: int, phase: int) -> int:
        """Scale hazard damage based on the active phase."""

        multiplier = 1.0 + self.damage_scale * max(0, phase - 1)
        return max(1, int(base_damage * multiplier))


LEVEL_CURVE = LevelCurve()

SPAWN_PHASES = {
    1: SpawnSchedule(base_interval=2.4, interval_decay=0.92, max_density=12),
    2: SpawnSchedule(base_interval=1.8, interval_decay=0.9, max_density=18),
    3: SpawnSchedule(base_interval=1.4, interval_decay=0.88, max_density=24),
    4: SpawnSchedule(base_interval=1.1, interval_decay=0.85, max_density=30),
}

HAZARD_PHASES = {
    1: HazardSchedule(base_interval=45.0, interval_variance=10.0, damage_scale=0.08),
    2: HazardSchedule(base_interval=42.0, interval_variance=9.0, damage_scale=0.1),
    3: HazardSchedule(base_interval=38.0, interval_variance=8.0, damage_scale=0.12),
    4: HazardSchedule(base_interval=34.0, interval_variance=7.5, damage_scale=0.15),
}

PHASE_BIOMES = {
    1: "Graveyard",
    2: "Abandoned Village",
    3: "Moonlit Forest",
    4: "Moonlit Forest",
}

GLYPH_SET_SIZE = 4
MAX_UPGRADE_OPTIONS = 3

