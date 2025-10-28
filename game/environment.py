"""Environment systems controlling biome hazards and dynamic events."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Sequence

from . import config


@dataclass(frozen=True)
class HazardBlueprint:
    """Defines the template for a biome hazard prior to scaling."""

    name: str
    description: str
    base_damage: int
    slow: float
    duration: float


@dataclass
class HazardEvent:
    """Represents a resolved hazard event applied to the run."""

    biome: str
    name: str
    description: str
    damage: int
    slow: float
    duration: float


_BIOME_HAZARDS: Dict[str, Sequence[HazardBlueprint]] = {
    "Graveyard": (
        HazardBlueprint(
            name="Creeping Fog",
            description="A chill fog settles in, sapping vitality and obscuring sight.",
            base_damage=6,
            slow=0.1,
            duration=8.0,
        ),
        HazardBlueprint(
            name="Spiteful Mausoleum",
            description="Spectral hands erupt from tombs, clawing at the hunter.",
            base_damage=9,
            slow=0.0,
            duration=4.0,
        ),
    ),
    "Abandoned Village": (
        HazardBlueprint(
            name="Falling Debris",
            description="Crumbling rooftops rain debris across the lane.",
            base_damage=11,
            slow=0.15,
            duration=5.0,
        ),
        HazardBlueprint(
            name="Lantern Burst",
            description="Bursting oil lanterns ignite patches of ground.",
            base_damage=13,
            slow=0.05,
            duration=6.0,
        ),
    ),
    "Moonlit Forest": (
        HazardBlueprint(
            name="Snaring Vines",
            description="Verdant tendrils lash out, hindering movement.",
            base_damage=14,
            slow=0.2,
            duration=7.0,
        ),
        HazardBlueprint(
            name="Wisp Surge",
            description="Arcane wisps discharge volatile energy in bursts.",
            base_damage=16,
            slow=0.0,
            duration=5.5,
        ),
    ),
}


def hazards_for_phase(phase: int) -> Sequence[HazardBlueprint]:
    """Return hazard options available to a given phase."""

    biome = config.PHASE_BIOMES.get(phase)
    if biome is None:
        raise ValueError(f"no biome configured for phase {phase}")
    return _BIOME_HAZARDS[biome]


class EnvironmentDirector:
    """Schedules hazards based on the active phase and biome."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._cooldowns = {
            phase: config.HAZARD_PHASES[phase].roll_interval(self._rng)
            for phase in config.HAZARD_PHASES
        }

    def update(self, phase: int, delta_time: float) -> List[HazardEvent]:
        """Advance timers and emit any hazards that should trigger."""

        schedule = config.HAZARD_PHASES[phase]
        self._cooldowns[phase] -= delta_time
        events: List[HazardEvent] = []

        while self._cooldowns[phase] <= 0:
            blueprint = self._rng.choice(tuple(hazards_for_phase(phase)))
            damage = schedule.scale_damage(blueprint.base_damage, phase)
            biome = config.PHASE_BIOMES[phase]
            events.append(
                HazardEvent(
                    biome=biome,
                    name=blueprint.name,
                    description=blueprint.description,
                    damage=damage,
                    slow=blueprint.slow,
                    duration=blueprint.duration,
                )
            )
            self._cooldowns[phase] += schedule.roll_interval(self._rng)

        return events

