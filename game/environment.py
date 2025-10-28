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


@dataclass(frozen=True)
class BarricadeBlueprint:
    """Defines destructible obstacles sprinkled through each biome."""

    name: str
    description: str
    durability: int
    salvage_reward: int


@dataclass
class BarricadeEvent:
    """Represents a barricade broken by the player's advance."""

    biome: str
    name: str
    description: str
    durability: int
    salvage_reward: int


@dataclass(frozen=True)
class ResourceCache:
    """Ambient caches that can be collected mid-run."""

    name: str
    description: str
    base_amount: int


@dataclass
class ResourceDropEvent:
    """Represents a loose cache discovered in the environment."""

    biome: str
    name: str
    description: str
    amount: int


@dataclass(frozen=True)
class WeatherPattern:
    """Defines a dynamic weather effect for a biome."""

    name: str
    description: str
    movement_modifier: float
    vision_modifier: float


@dataclass
class WeatherEvent:
    """Represents the start or end of a weather pattern."""

    biome: str
    name: str
    description: str
    movement_modifier: float
    vision_modifier: float
    duration: float
    ended: bool = False


@dataclass
class EnvironmentTickResult:
    """Aggregated environment outputs for a simulation step."""

    hazards: List[HazardEvent]
    barricades: List[BarricadeEvent]
    resource_drops: List[ResourceDropEvent]
    weather_events: List[WeatherEvent]


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


_BIOME_BARRICADES: Dict[str, Sequence[BarricadeBlueprint]] = {
    "Graveyard": (
        BarricadeBlueprint(
            name="Rotting Palisade",
            description="Splintered stakes jut from the soil, slowing the hunter's stride.",
            durability=18,
            salvage_reward=6,
        ),
        BarricadeBlueprint(
            name="Crumbling Coffin Cart",
            description="Abandoned cart spills decrepit coffins across the lane.",
            durability=24,
            salvage_reward=8,
        ),
    ),
    "Abandoned Village": (
        BarricadeBlueprint(
            name="Collapsed Market Stall",
            description="Tattered cloth and timber form a makeshift barrier.",
            durability=30,
            salvage_reward=10,
        ),
        BarricadeBlueprint(
            name="Shuttered Doorway",
            description="Barricaded homes block the main thoroughfare.",
            durability=36,
            salvage_reward=12,
        ),
    ),
    "Moonlit Forest": (
        BarricadeBlueprint(
            name="Thorned Bramble Wall",
            description="Entwined vines bristle with razor thorns.",
            durability=34,
            salvage_reward=11,
        ),
        BarricadeBlueprint(
            name="Ancient Root Snare",
            description="Gnarled roots coil from colossal trees, sealing the path.",
            durability=40,
            salvage_reward=14,
        ),
    ),
}


_RESOURCE_CACHES: Dict[str, Sequence[ResourceCache]] = {
    "Graveyard": (
        ResourceCache(
            name="Soul Jar",
            description="Ceramic urn brimming with reclaimed soul shards.",
            base_amount=5,
        ),
        ResourceCache(
            name="Vigil Candle",
            description="A flickering candle melts into alchemical wax usable as salvage.",
            base_amount=7,
        ),
    ),
    "Abandoned Village": (
        ResourceCache(
            name="Supply Satchel",
            description="Forgotten militia gear yields usable components.",
            base_amount=8,
        ),
        ResourceCache(
            name="Merchant Strongbox",
            description="A cracked lockbox spills coin and brass fittings.",
            base_amount=10,
        ),
    ),
    "Moonlit Forest": (
        ResourceCache(
            name="Glowcap Cluster",
            description="Bioluminescent fungi harvested for potent reagents.",
            base_amount=11,
        ),
        ResourceCache(
            name="Ancient Effigy",
            description="Runed effigy crumbles into empowering glyph dust.",
            base_amount=13,
        ),
    ),
}


_WEATHER_PATTERNS: Dict[str, Sequence[WeatherPattern]] = {
    "Graveyard": (
        WeatherPattern(
            name="Grave Chill",
            description="A supernatural cold rolls through, numbing limbs.",
            movement_modifier=-0.1,
            vision_modifier=-0.05,
        ),
        WeatherPattern(
            name="Lantern Vigil",
            description="Caretaker spirits illuminate the grounds, easing aim.",
            movement_modifier=0.0,
            vision_modifier=0.08,
        ),
    ),
    "Abandoned Village": (
        WeatherPattern(
            name="Ashen Gusts",
            description="Sooty winds whip through the alleys, biting at exposed skin.",
            movement_modifier=-0.08,
            vision_modifier=-0.07,
        ),
        WeatherPattern(
            name="Moonlit Break",
            description="Clouds part, bathing the village in guiding moonlight.",
            movement_modifier=0.05,
            vision_modifier=0.06,
        ),
    ),
    "Moonlit Forest": (
        WeatherPattern(
            name="Phosphor Rain",
            description="Glowing droplets invigorate strides but distort visibility.",
            movement_modifier=0.07,
            vision_modifier=-0.05,
        ),
        WeatherPattern(
            name="Silver Gale",
            description="Cutting winds howl through the canopy, slowing progress.",
            movement_modifier=-0.12,
            vision_modifier=0.04,
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
        self._barricade_cooldowns = {
            phase: config.BARRICADE_PHASES[phase].roll_interval(self._rng)
            for phase in config.BARRICADE_PHASES
        }
        self._resource_cooldowns = {
            phase: config.RESOURCE_PHASES[phase].roll_interval(self._rng)
            for phase in config.RESOURCE_PHASES
        }
        self._weather_cooldowns = {
            phase: config.WEATHER_PHASES[phase].roll_interval(self._rng)
            for phase in config.WEATHER_PHASES
        }
        self._weather_durations = {phase: 0.0 for phase in config.WEATHER_PHASES}
        self._active_weather: Dict[int, WeatherEvent | None] = {phase: None for phase in config.WEATHER_PHASES}

    def update(self, phase: int, delta_time: float) -> EnvironmentTickResult:
        """Advance timers and emit any environment outputs that should trigger."""

        schedule = config.HAZARD_PHASES[phase]
        self._cooldowns[phase] -= delta_time
        hazards: List[HazardEvent] = []

        while self._cooldowns[phase] <= 0:
            blueprint = self._rng.choice(tuple(hazards_for_phase(phase)))
            damage = schedule.scale_damage(blueprint.base_damage, phase)
            biome = config.PHASE_BIOMES[phase]
            hazards.append(
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

        barricades: List[BarricadeEvent] = []
        barricade_schedule = config.BARRICADE_PHASES[phase]
        self._barricade_cooldowns[phase] -= delta_time
        biome = config.PHASE_BIOMES[phase]

        while self._barricade_cooldowns[phase] <= 0:
            blueprint = self._rng.choice(tuple(_BIOME_BARRICADES[biome]))
            salvage = barricade_schedule.scale_reward(blueprint.salvage_reward, phase)
            barricades.append(
                BarricadeEvent(
                    biome=biome,
                    name=blueprint.name,
                    description=blueprint.description,
                    durability=blueprint.durability,
                    salvage_reward=salvage,
                )
            )
            self._barricade_cooldowns[phase] += barricade_schedule.roll_interval(self._rng)

        resource_drops: List[ResourceDropEvent] = []
        resource_schedule = config.RESOURCE_PHASES[phase]
        self._resource_cooldowns[phase] -= delta_time

        while self._resource_cooldowns[phase] <= 0:
            cache = self._rng.choice(tuple(_RESOURCE_CACHES[biome]))
            amount = resource_schedule.scale_amount(cache.base_amount, phase)
            resource_drops.append(
                ResourceDropEvent(
                    biome=biome,
                    name=cache.name,
                    description=cache.description,
                    amount=amount,
                )
            )
            self._resource_cooldowns[phase] += resource_schedule.roll_interval(self._rng)

        weather_events: List[WeatherEvent] = []
        weather_schedule = config.WEATHER_PHASES[phase]
        self._weather_cooldowns[phase] -= delta_time
        if self._active_weather[phase]:
            self._weather_durations[phase] -= delta_time
            if self._weather_durations[phase] <= 0:
                active = self._active_weather[phase]
                weather_events.append(
                    WeatherEvent(
                        biome=active.biome,
                        name=f"{active.name} Fades",
                        description="The atmosphere calms, restoring baseline footing.",
                        movement_modifier=0.0,
                        vision_modifier=0.0,
                        duration=0.0,
                        ended=True,
                    )
                )
                self._active_weather[phase] = None

        if self._weather_cooldowns[phase] <= 0:
            pattern = self._rng.choice(tuple(_WEATHER_PATTERNS[biome]))
            duration = weather_schedule.roll_duration(self._rng)
            event = WeatherEvent(
                biome=biome,
                name=pattern.name,
                description=pattern.description,
                movement_modifier=pattern.movement_modifier,
                vision_modifier=pattern.vision_modifier,
                duration=duration,
            )
            weather_events.append(event)
            self._active_weather[phase] = event
            self._weather_durations[phase] = duration
            self._weather_cooldowns[phase] += weather_schedule.roll_interval(self._rng)

        return EnvironmentTickResult(
            hazards=hazards,
            barricades=barricades,
            resource_drops=resource_drops,
            weather_events=weather_events,
        )

