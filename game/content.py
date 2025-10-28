"""Content definitions used to drive encounter generation."""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Sequence

from . import config
from .entities import Enemy, WaveDescriptor

# Enemy archetype blueprints roughly aligned with the PRD's enemy list.
_BASE_ENEMY_ARCHETYPES: Dict[str, Dict[str, float]] = {
    "Swarm Thrall": {"health": 24, "damage": 4, "speed": 1.6},
    "Grave Bat": {"health": 18, "damage": 5, "speed": 2.0},
    "Blight Crawler": {"health": 30, "damage": 6, "speed": 1.5},
    "Bone Stalker": {"health": 55, "damage": 10, "speed": 1.1},
    "Occultist": {"health": 32, "damage": 8, "speed": 1.2},
    "Hollow Archer": {"health": 42, "damage": 9, "speed": 1.3},
    "Crypt Bruiser": {"health": 110, "damage": 16, "speed": 0.75},
    "Howling Shade": {"health": 40, "damage": 12, "speed": 1.4},
    "Wailing Siren": {"health": 58, "damage": 13, "speed": 1.1},
    "Dread Pyre": {"health": 65, "damage": 14, "speed": 1.0},
    "Night Reaper": {"health": 48, "damage": 20, "speed": 1.35},
    "Ashen Rider": {"health": 90, "damage": 18, "speed": 1.05},
}


_ELITE_ENEMY_ARCHETYPES: Dict[str, Dict[str, float]] = {
    "Crypt Juggernaut": {"health": 180, "damage": 28, "speed": 0.8},
    "Storm Revenant": {"health": 140, "damage": 24, "speed": 1.35},
    "Grave Titan": {"health": 220, "damage": 32, "speed": 0.7},
    "Infernal Sovereign": {"health": 190, "damage": 34, "speed": 1.0},
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
    "Gravemind Bloom",
    "Astral Needle",
    "Chillwyrm Scale",
    "Inferno Brand",
    "Verdant Heart",
    "Clockwork Sigil",
    "Duskwalker Boots",
    "Siren's Locket",
    "Juggernaut Core",
    "Wraith Candle",
    "Lantern of Dawn",
    "Gauntlet Coil",
    "Frostglass Rosary",
    "Umbral Codex",
)


_FINAL_BOSS_BLUEPRINT = {
    "name": "Dawn Revenant",
    "phases": (
        {"health": 640, "damage": 42, "speed": 1.05},
        {"health": 520, "damage": 50, "speed": 1.18},
        {"health": 460, "damage": 60, "speed": 1.3},
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
    return Enemy(name=str(blueprint["name"]), health=health, damage=damage, speed=float(blueprint["speed"]))


def draw_relic(rng: random.Random) -> str:
    """Return a relic reward name."""

    return rng.choice(_RELIC_LIBRARY)


def relic_catalog() -> Sequence[str]:
    """Expose the full relic catalog for validation and tooling."""

    return list(_RELIC_LIBRARY)


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
        phases.append(
            Enemy(
                name=f"{name} (Phase {index})",
                health=int(phase["health"]),
                damage=int(phase["damage"]),
                speed=float(phase["speed"]),
            )
        )
    return phases

