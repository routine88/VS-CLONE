"""Content definitions used to drive encounter generation."""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Sequence, Tuple

from . import config
from .entities import Enemy, EnemyLane, WaveDescriptor
from .relics import relic_names

# Enemy archetype blueprints roughly aligned with the PRD's enemy list.
_BASE_ENEMY_ARCHETYPES: Dict[str, Dict[str, object]] = {
    "Swarm Thrall": {
        "health": 24,
        "damage": 4,
        "speed": 1.6,
        "lane": EnemyLane.GROUND,
        "behaviors": ("pursuit",),
    },
    "Grave Bat": {
        "health": 18,
        "damage": 5,
        "speed": 2.0,
        "lane": EnemyLane.AIR,
        "behaviors": ("swoop",),
    },
    "Blight Crawler": {
        "health": 30,
        "damage": 6,
        "speed": 1.5,
        "lane": EnemyLane.GROUND,
        "behaviors": ("burrow",),
    },
    "Bone Stalker": {
        "health": 55,
        "damage": 10,
        "speed": 1.1,
        "lane": EnemyLane.GROUND,
        "behaviors": ("pursuit", "shield"),
    },
    "Occultist": {
        "health": 32,
        "damage": 8,
        "speed": 1.2,
        "lane": EnemyLane.GROUND,
        "behaviors": ("ranged",),
    },
    "Hollow Archer": {
        "health": 42,
        "damage": 9,
        "speed": 1.3,
        "lane": EnemyLane.GROUND,
        "behaviors": ("ranged",),
    },
    "Crypt Bruiser": {
        "health": 110,
        "damage": 16,
        "speed": 0.75,
        "lane": EnemyLane.GROUND,
        "behaviors": ("pursuit", "stagger"),
    },
    "Howling Shade": {
        "health": 40,
        "damage": 12,
        "speed": 1.4,
        "lane": EnemyLane.AIR,
        "behaviors": ("wail", "ranged"),
    },
    "Wailing Siren": {
        "health": 58,
        "damage": 13,
        "speed": 1.1,
        "lane": EnemyLane.AIR,
        "behaviors": ("wail", "slow"),
    },
    "Dread Pyre": {
        "health": 65,
        "damage": 14,
        "speed": 1.0,
        "lane": EnemyLane.AIR,
        "behaviors": ("kamikaze",),
    },
    "Night Reaper": {
        "health": 48,
        "damage": 20,
        "speed": 1.35,
        "lane": EnemyLane.GROUND,
        "behaviors": ("dash",),
    },
    "Ashen Rider": {
        "health": 90,
        "damage": 18,
        "speed": 1.05,
        "lane": EnemyLane.CEILING,
        "behaviors": ("clinger", "pounce"),
    },
}


_ELITE_ENEMY_ARCHETYPES: Dict[str, Dict[str, object]] = {
    "Crypt Juggernaut": {
        "health": 180,
        "damage": 28,
        "speed": 0.8,
        "lane": EnemyLane.GROUND,
        "behaviors": ("stagger", "shield"),
    },
    "Storm Revenant": {
        "health": 140,
        "damage": 24,
        "speed": 1.35,
        "lane": EnemyLane.AIR,
        "behaviors": ("ranged", "dash"),
    },
    "Grave Titan": {
        "health": 220,
        "damage": 32,
        "speed": 0.7,
        "lane": EnemyLane.GROUND,
        "behaviors": ("shockwave",),
    },
    "Infernal Sovereign": {
        "health": 190,
        "damage": 34,
        "speed": 1.0,
        "lane": EnemyLane.CEILING,
        "behaviors": ("clinger", "ranged"),
    },
}


_PHASE_BASE_ARCHETYPES: Dict[int, Sequence[str]] = {
    1: ("Swarm Thrall", "Grave Bat", "Blight Crawler"),
    2: ("Bone Stalker", "Occultist", "Hollow Archer"),
    3: ("Crypt Bruiser", "Howling Shade", "Wailing Siren"),
    4: ("Dread Pyre", "Night Reaper", "Ashen Rider"),
}


_PHASE_ELITE_ARCHETYPES: Dict[int, Sequence[str]] = {
    3: ("Crypt Juggernaut", "Storm Revenant"),
    4: ("Crypt Juggernaut", "Storm Revenant", "Grave Titan", "Infernal Sovereign"),
}


_ELITE_SPAWN_CHANCE: Dict[int, float] = {
    3: 0.12,
    4: 0.2,
}


_MINIBOSS_BLUEPRINTS: Sequence[Dict[str, object]] = (
    {
        "name": "Crimson Warden",
        "min_phase": 1,
        "health": 360,
        "damage": 22,
        "speed": 0.9,
        "lane": EnemyLane.GROUND,
        "behaviors": ("pursuit", "shield"),
    },
    {
        "name": "Storm Herald",
        "min_phase": 2,
        "health": 420,
        "damage": 26,
        "speed": 1.0,
        "lane": EnemyLane.AIR,
        "behaviors": ("ranged", "dash"),
    },
    {
        "name": "Clockwork Behemoth",
        "min_phase": 3,
        "health": 520,
        "damage": 32,
        "speed": 0.8,
        "lane": EnemyLane.GROUND,
        "behaviors": ("shockwave", "stagger"),
    },
    {
        "name": "Infernal Matriarch",
        "min_phase": 4,
        "health": 640,
        "damage": 38,
        "speed": 1.05,
        "lane": EnemyLane.CEILING,
        "behaviors": ("clinger", "ranged"),
    },
)


_FINAL_BOSS_BLUEPRINT = {
    "name": "Dawn Revenant",
    "phases": (
        {
            "health": 640,
            "damage": 42,
            "speed": 1.05,
            "lane": EnemyLane.GROUND,
            "behaviors": ("shockwave",),
        },
        {
            "health": 520,
            "damage": 50,
            "speed": 1.18,
            "lane": EnemyLane.AIR,
            "behaviors": ("ranged", "dash"),
        },
        {
            "health": 460,
            "damage": 60,
            "speed": 1.3,
            "lane": EnemyLane.CEILING,
            "behaviors": ("clinger", "kamikaze"),
        },
    ),
}


def enemy_archetypes_for_phase(phase: int) -> List[str]:
    """Return the list of base archetypes available for the requested phase."""

    archetypes: List[str] = []
    for step in range(1, phase + 1):
        archetypes.extend(_PHASE_BASE_ARCHETYPES.get(step, ()))
    return _dedupe(archetypes)


def elite_archetypes_for_phase(phase: int) -> List[str]:
    """Return elite archetypes unlocked by the requested phase."""

    elites: List[str] = []
    for step in range(1, phase + 1):
        elites.extend(_PHASE_ELITE_ARCHETYPES.get(step, ()))
    return _dedupe(elites)


def instantiate_enemy(name: str, scale: float) -> Enemy:
    """Return a scaled instance of the given enemy archetype."""

    blueprint = _BASE_ENEMY_ARCHETYPES.get(name)
    if blueprint is None:
        blueprint = _ELITE_ENEMY_ARCHETYPES.get(name)
    if blueprint is None:
        raise ValueError(f"unknown enemy archetype: {name}")
    health = max(1, int(float(blueprint["health"]) * scale))
    damage = max(1, int(float(blueprint["damage"]) * scale))
    lane = blueprint.get("lane", EnemyLane.GROUND)
    behaviors: Tuple[str, ...]
    raw_behaviors = blueprint.get("behaviors", ())
    if isinstance(raw_behaviors, tuple):
        behaviors = raw_behaviors
    elif isinstance(raw_behaviors, list):
        behaviors = tuple(raw_behaviors)
    else:
        behaviors = (str(raw_behaviors),) if raw_behaviors else ()
    if isinstance(lane, EnemyLane):
        lane_value = lane.value
    else:
        lane_value = str(lane)
    return Enemy(
        name=name,
        health=health,
        damage=damage,
        speed=float(blueprint["speed"]),
        lane=EnemyLane(lane_value),
        behaviors=behaviors,
    )


def build_wave_descriptor(
    phase: int,
    wave_index: int,
    rng: random.Random,
) -> WaveDescriptor:
    """Create a wave descriptor with scaling aligned to phase and wave."""

    schedule = config.SPAWN_PHASES[phase]
    base_count = 6 + (phase - 1) * 2
    count_growth = wave_index * 2
    enemy_count = min(schedule.max_density, base_count + count_growth)

    phase_scale = 1.0 + 0.18 * (phase - 1)
    wave_scale = 1.0 + 0.06 * wave_index
    scale = phase_scale * wave_scale

    pool = enemy_archetypes_for_phase(phase)
    enemies = [instantiate_enemy(rng.choice(pool), scale) for _ in range(enemy_count)]

    elite_chance = _ELITE_SPAWN_CHANCE.get(phase, 0.0)
    elite_pool = elite_archetypes_for_phase(phase)
    if elite_pool and elite_chance > 0:
        for index in range(len(enemies)):
            if rng.random() < elite_chance:
                elite_name = rng.choice(elite_pool)
                enemies[index] = instantiate_enemy(elite_name, scale * 1.15)
    return WaveDescriptor(phase=phase, wave_index=wave_index, enemies=enemies)


def pick_miniboss(phase: int, rng: random.Random) -> Enemy:
    """Select a miniboss blueprint eligible for the current phase."""

    candidates = [bp for bp in _MINIBOSS_BLUEPRINTS if phase >= int(bp["min_phase"])]
    blueprint = rng.choice(candidates)
    scale = 1.0 + 0.12 * (phase - int(blueprint["min_phase"]))
    health = int(float(blueprint["health"]) * scale)
    damage = int(float(blueprint["damage"]) * scale)
    lane = blueprint.get("lane", EnemyLane.GROUND.value)
    lane_value = lane.value if isinstance(lane, EnemyLane) else str(lane)
    behaviors = tuple(blueprint.get("behaviors", ()))
    return Enemy(
        name=str(blueprint["name"]),
        health=health,
        damage=damage,
        speed=float(blueprint["speed"]),
        lane=EnemyLane(lane_value),
        behaviors=behaviors,
    )


def draw_relic(rng: random.Random) -> str:
    """Return a relic reward name."""

    return rng.choice(relic_names())


def relic_catalog() -> Sequence[str]:
    """Expose the full relic catalog for validation and tooling."""

    return list(relic_names())


def _dedupe(items: Iterable[str]) -> List[str]:
    """Preserve order while removing duplicates."""

    seen: Dict[str, None] = {}
    for name in items:
        seen.setdefault(name, None)
    return list(seen.keys())


def final_boss_phases() -> List[Enemy]:
    """Return the phase descriptors for the final boss encounter."""

    phases: List[Enemy] = []
    blueprint = _FINAL_BOSS_BLUEPRINT
    name = str(blueprint["name"])
    for index, phase in enumerate(blueprint["phases"], start=1):
        lane = phase.get("lane", EnemyLane.GROUND)
        if isinstance(lane, EnemyLane):
            lane_value = lane.value
        else:
            lane_value = str(lane)
        phases.append(
            Enemy(
                name=f"{name} (Phase {index})",
                health=int(phase["health"]),
                damage=int(phase["damage"]),
                speed=float(phase["speed"]),
                lane=EnemyLane(lane_value),
                behaviors=tuple(phase.get("behaviors", ())),
            )
        )
    return phases

