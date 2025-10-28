"""Content definitions used to drive encounter generation."""

from __future__ import annotations

import random
from typing import Dict, List, Sequence

from . import config
from .entities import Enemy, WaveDescriptor

# Enemy archetype blueprints roughly aligned with the PRD's enemy list.
_ENEMY_ARCHETYPES: Dict[str, Dict[str, float]] = {
    "Swarm Thrall": {"health": 24, "damage": 4, "speed": 1.6},
    "Grave Bat": {"health": 18, "damage": 5, "speed": 2.0},
    "Bone Stalker": {"health": 55, "damage": 10, "speed": 1.1},
    "Occultist": {"health": 32, "damage": 8, "speed": 1.2},
    "Crypt Bruiser": {"health": 110, "damage": 16, "speed": 0.75},
    "Howling Shade": {"health": 40, "damage": 12, "speed": 1.4},
    "Dread Pyre": {"health": 65, "damage": 14, "speed": 1.0},
    "Night Reaper": {"health": 48, "damage": 20, "speed": 1.35},
}


_PHASE_ARCHETYPES: Dict[int, Sequence[str]] = {
    1: ("Swarm Thrall", "Grave Bat"),
    2: ("Bone Stalker", "Occultist"),
    3: ("Crypt Bruiser", "Howling Shade"),
    4: ("Dread Pyre", "Night Reaper"),
}


_MINIBOSS_BLUEPRINTS: Sequence[Dict[str, object]] = (
    {"name": "Crimson Warden", "min_phase": 1, "health": 360, "damage": 22, "speed": 0.9},
    {"name": "Storm Herald", "min_phase": 2, "health": 420, "damage": 26, "speed": 1.0},
    {"name": "Clockwork Behemoth", "min_phase": 3, "health": 520, "damage": 32, "speed": 0.8},
    {"name": "Infernal Matriarch", "min_phase": 4, "health": 640, "damage": 38, "speed": 1.05},
)


_RELIC_LIBRARY: Sequence[str] = (
    "Moonlit Charm",
    "Storm Prism",
    "Blood Chalice",
    "Gale Idols",
    "Iron Bark Totem",
    "Phoenix Ember",
)


def enemy_archetypes_for_phase(phase: int) -> List[str]:
    """Return the list of archetypes available for the requested phase."""

    archetypes: List[str] = []
    for step in range(1, phase + 1):
        archetypes.extend(_PHASE_ARCHETYPES.get(step, ()))
    # Preserve order while removing duplicates.
    seen: Dict[str, None] = {}
    for name in archetypes:
        seen.setdefault(name, None)
    return list(seen.keys())


def instantiate_enemy(name: str, scale: float) -> Enemy:
    """Return a scaled instance of the given enemy archetype."""

    try:
        blueprint = _ENEMY_ARCHETYPES[name]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"unknown enemy archetype: {name}") from exc
    health = max(1, int(blueprint["health"] * scale))
    damage = max(1, int(blueprint["damage"] * scale))
    return Enemy(name=name, health=health, damage=damage, speed=float(blueprint["speed"]))


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
    return WaveDescriptor(phase=phase, wave_index=wave_index, enemies=enemies)


def pick_miniboss(phase: int, rng: random.Random) -> Enemy:
    """Select a miniboss blueprint eligible for the current phase."""

    candidates = [bp for bp in _MINIBOSS_BLUEPRINTS if phase >= int(bp["min_phase"])]
    blueprint = rng.choice(candidates)
    scale = 1.0 + 0.12 * (phase - int(blueprint["min_phase"]))
    health = int(float(blueprint["health"]) * scale)
    damage = int(float(blueprint["damage"]) * scale)
    return Enemy(name=str(blueprint["name"]), health=health, damage=damage, speed=float(blueprint["speed"]))


def draw_relic(rng: random.Random) -> str:
    """Return a relic reward name."""

    return rng.choice(_RELIC_LIBRARY)

