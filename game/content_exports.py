"""Structured content exports consumed by the native runtime importer."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from . import combat, config, content, environment
from .entities import EnemyLane, GlyphFamily
from .game_state import weapon_upgrade_paths
from .profile import default_hunters
from .relics import relic_definitions

_LAUNCH_HUNTERS: Sequence[str] = ("hunter_varik", "hunter_mira")

_HUNTER_ABILITY_PAYLOADS: Mapping[str, Dict[str, Any]] = {
    "hunter_varik": {
        "dash": {"cooldown": 2.0, "strength": 26.0},
    },
    "hunter_mira": {
        "dash": {"cooldown": 2.0, "strength": 26.0},
    },
}

_WEAPON_SYNERGIES: Mapping[str, Dict[str, Any]] = {
    "Dusk Repeater": {
        "id": "weapon_dusk_repeater",
        "glyph": GlyphFamily.BLOOD,
        "role": "ranged_burst",
        "description": "Signature repeater that channels blood glyphs into lifesteal volleys.",
        "ultimate": "Consumes a Blood Sigil set to fire a draining volley that heals for 8% of damage dealt.",
    },
    "Storm Siphon": {
        "id": "weapon_storm_siphon",
        "glyph": GlyphFamily.STORM,
        "role": "piercing_beam",
        "description": "Arc conduit that leaps between foes, scaling with storm glyphs.",
        "ultimate": "With four Storm Sigils active, beams fork twice, chaining to nearby elites automatically.",
    },
    "Gravebloom Staff": {
        "id": "weapon_gravebloom_staff",
        "glyph": GlyphFamily.VERDANT,
        "role": "area_control",
        "description": "Seeds necrotic blooms whose poison clouds fatten with verdant glyphs.",
        "ultimate": "Completing a Verdant Sigil set causes blooms to explode into healing spores for the hunter.",
    },
    "Inferno Lantern": {
        "id": "weapon_inferno_lantern",
        "glyph": GlyphFamily.INFERNO,
        "role": "lingering_burn",
        "description": "Suspends fire wisps that orbit and scorch lanes, empowered by inferno glyphs.",
        "ultimate": "At four Inferno Sigils, lantern wisps detonate, leaving a burning corridor for 6 seconds.",
    },
}


def build_content_bundle() -> Dict[str, Any]:
    """Return the combined content payload expected by the runtime."""

    return {
        "version": "vertical_slice_graveyard_v1",
        "progression": progression_payload(),
        "biomes": [graveyard_biome_payload()],
        "hunters": launch_hunter_payloads(),
        "weapons": glyph_synergy_weapon_payloads(),
        "relics": relic_payloads(),
    }


def graveyard_biome_payload() -> Dict[str, Any]:
    """Generate the encounter payload for the Graveyard biome."""

    phases: List[Dict[str, Any]] = []
    environment_entries: List[Dict[str, Any]] = []
    enemy_catalog = content.enemy_blueprints(include_elites=True)
    miniboss_entries = content.miniboss_blueprints()

    for phase in range(1, 5):
        environment_entries.append(_environment_phase_payload(phase))
        phases.append(
            {
                "id": f"graveyard_phase_{phase}",
                "phase": phase,
                "balance": _phase_balance_payload(phase),
                "enemy_roster": [_enemy_payload(enemy_catalog[name]) for name in content.enemy_archetypes_for_phase(phase)],
                "elite_roster": [
                    _enemy_payload(enemy_catalog[name]) for name in content.elite_archetypes_for_phase(phase)
                ],
                "minibosses": [
                    _miniboss_payload(entry)
                    for entry in miniboss_entries
                    if phase >= int(entry.get("min_phase", 1))
                ],
            }
        )

    boss = _final_boss_payload(content.final_boss_blueprint())

    return {
        "id": "biome_graveyard",
        "name": "Neon Graveyard",
        "description": "A neon-lit necropolis with layered sightlines and relentless undead hordes.",
        "phases": phases,
        "environment": environment_entries,
        "final_boss": boss,
    }


def progression_payload() -> Dict[str, Any]:
    """Expose progression constants used by the runtime UI."""

    return {
        "glyph_set_size": int(config.GLYPH_SET_SIZE),
        "max_upgrade_options": int(config.MAX_UPGRADE_OPTIONS),
        "run_duration_seconds": int(config.RUN_DURATION_SECONDS),
    }


def relic_payloads() -> List[Dict[str, Any]]:
    """Return the relic catalogue with modifier breakdowns."""

    payload: List[Dict[str, Any]] = []
    for definition in relic_definitions():
        modifier = definition.modifier
        payload.append(
            {
                "id": definition.id,
                "name": definition.name,
                "description": definition.description,
                "modifier": {
                    "max_health": int(modifier.max_health),
                    "damage_scale": float(modifier.damage_scale),
                    "defense_scale": float(modifier.defense_scale),
                    "hazard_resist": float(modifier.hazard_resist),
                    "salvage_scale": float(modifier.salvage_scale),
                    "soul_scale": float(modifier.soul_scale),
                    "lifesteal_bonus": float(modifier.lifesteal_bonus),
                    "regen_per_second": float(modifier.regen_per_second),
                    "glyph_bonus": {
                        family.value: int(amount)
                        for family, amount in modifier.glyph_bonus.items()
                    },
                    "salvage_bonus_flat": int(modifier.salvage_bonus_flat),
                    "heal_on_pickup": int(modifier.heal_on_pickup),
                },
            }
        )
    return payload


def launch_hunter_payloads() -> List[Dict[str, Any]]:
    """Return the hunter roster earmarked for the vertical slice."""

    roster = default_hunters()
    payload: List[Dict[str, Any]] = []
    for hunter_id in _LAUNCH_HUNTERS:
        definition = roster[hunter_id]
        glyph_value = definition.signature_glyph.value if definition.signature_glyph else None
        starting_glyphs = [glyph_value] if glyph_value else []
        abilities = dict(_HUNTER_ABILITY_PAYLOADS.get(hunter_id, {}))
        payload.append(
            {
                "id": definition.id,
                "name": definition.name,
                "description": definition.description,
                "max_health": int(definition.max_health),
                "starting_weapon": definition.starting_weapon,
                "starting_weapon_tier": int(definition.starting_weapon_tier),
                "signature_glyph": glyph_value,
                "starting_glyphs": starting_glyphs,
                "abilities": abilities,
            }
        )
    return payload


def glyph_synergy_weapon_payloads() -> List[Dict[str, Any]]:
    """Return the glyph-synergy weapon table along with upgrade paths."""

    library = combat.weapon_library()
    upgrades = weapon_upgrade_paths()

    payload: List[Dict[str, Any]] = []
    for weapon, metadata in _WEAPON_SYNERGIES.items():
        tier_stats = library.get(weapon, {})
        tier_descriptions = upgrades.get(weapon, {})
        tiers: List[Dict[str, Any]] = []
        for tier in sorted(tier_stats.keys()):
            stats = tier_stats[tier]
            tiers.append(
                {
                    "tier": int(tier),
                    "damage": float(stats.damage),
                    "cooldown": float(stats.cooldown),
                    "projectiles": int(stats.projectiles),
                    "description": tier_descriptions.get(tier),
                }
            )
        payload.append(
            {
                "id": metadata.get("id", f"weapon_{_slug(weapon)}"),
                "name": weapon,
                "glyph_synergy": metadata["glyph"].value,
                "role": metadata.get("role", ""),
                "description": metadata.get("description", ""),
                "ultimate": metadata.get("ultimate"),
                "tiers": tiers,
            }
        )
    return payload


def _phase_balance_payload(phase: int) -> Dict[str, Any]:
    schedule = config.SPAWN_PHASES[phase]
    base_enemy_count = 6 + (phase - 1) * 2

    return {
        "spawn_schedule": {
            "base_interval": float(schedule.base_interval),
            "interval_decay": float(schedule.interval_decay),
            "max_density": int(schedule.max_density),
        },
        "wave_scaling": {
            "base_enemy_count": base_enemy_count,
            "per_wave_increment": 2,
            "phase_multiplier": round(1.0 + 0.18 * (phase - 1), 5),
            "per_wave_multiplier": 0.06,
        },
        "elite": {
            "spawn_chance": content.elite_spawn_chance(phase),
            "scale_multiplier": 1.15,
        },
    }


def _enemy_payload(entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "id": f"enemy_{_slug(str(entry['name']))}",
        "name": entry["name"],
        "category": entry.get("category", "base"),
        "health": int(entry["health"]),
        "damage": int(entry["damage"]),
        "speed": float(entry["speed"]),
        "lane": str(entry.get("lane", EnemyLane.GROUND.value)),
        "behaviors": list(entry.get("behaviors", ())),
    }


def _miniboss_payload(entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "id": f"miniboss_{_slug(str(entry['name']))}",
        "name": entry["name"],
        "min_phase": int(entry.get("min_phase", 1)),
        "health": int(entry["health"]),
        "damage": int(entry["damage"]),
        "speed": float(entry["speed"]),
        "lane": str(entry.get("lane", EnemyLane.GROUND.value)),
        "behaviors": list(entry.get("behaviors", ())),
    }


def _final_boss_payload(blueprint: Mapping[str, Any]) -> Dict[str, Any]:
    phases: List[Dict[str, Any]] = []
    for index, phase in enumerate(blueprint.get("phases", ()), start=1):
        phases.append(
            {
                "index": index,
                "health": int(phase["health"]),
                "damage": int(phase["damage"]),
                "speed": float(phase["speed"]),
                "lane": str(phase.get("lane", EnemyLane.GROUND.value)),
                "behaviors": list(phase.get("behaviors", ())),
            }
        )
    return {
        "id": "boss_dawn_revenant",
        "name": str(blueprint.get("name", "")),
        "phases": phases,
    }


def _environment_phase_payload(phase: int) -> Dict[str, Any]:
    biome = config.PHASE_BIOMES[phase]
    hazards = [
        _hazard_payload(entry) for entry in environment.hazard_blueprints_for_biome(biome)
    ]
    barricades = [
        _barricade_payload(entry)
        for entry in environment.barricade_blueprints_for_biome(biome)
    ]
    caches = [
        _resource_cache_payload(entry)
        for entry in environment.resource_caches_for_biome(biome)
    ]
    weather_patterns = [
        _weather_payload(entry)
        for entry in environment.weather_patterns_for_biome(biome)
    ]

    schedules = {
        "hazard": _hazard_schedule_payload(config.HAZARD_PHASES[phase]),
        "barricade": _barricade_schedule_payload(config.BARRICADE_PHASES[phase]),
        "resource": _resource_schedule_payload(config.RESOURCE_PHASES[phase]),
        "weather": _weather_schedule_payload(config.WEATHER_PHASES[phase]),
    }

    return {
        "phase": int(phase),
        "biome": biome,
        "hazards": hazards,
        "barricades": barricades,
        "resource_caches": caches,
        "weather_patterns": weather_patterns,
        "schedules": schedules,
    }


def _hazard_payload(blueprint: environment.HazardBlueprint) -> Dict[str, Any]:
    return {
        "id": f"hazard_{_slug(blueprint.name)}",
        "name": blueprint.name,
        "description": blueprint.description,
        "base_damage": int(blueprint.base_damage),
        "slow": float(blueprint.slow),
        "duration": float(blueprint.duration),
    }


def _barricade_payload(blueprint: environment.BarricadeBlueprint) -> Dict[str, Any]:
    return {
        "id": f"barricade_{_slug(blueprint.name)}",
        "name": blueprint.name,
        "description": blueprint.description,
        "durability": int(blueprint.durability),
        "salvage_reward": int(blueprint.salvage_reward),
    }


def _resource_cache_payload(cache: environment.ResourceCache) -> Dict[str, Any]:
    return {
        "id": f"cache_{_slug(cache.name)}",
        "name": cache.name,
        "description": cache.description,
        "base_amount": int(cache.base_amount),
    }


def _weather_payload(pattern: environment.WeatherPattern) -> Dict[str, Any]:
    return {
        "id": f"weather_{_slug(pattern.name)}",
        "name": pattern.name,
        "description": pattern.description,
        "movement_modifier": float(pattern.movement_modifier),
        "vision_modifier": float(pattern.vision_modifier),
    }


def _hazard_schedule_payload(schedule: config.HazardSchedule) -> Dict[str, Any]:
    return {
        "base_interval": float(schedule.base_interval),
        "interval_variance": float(schedule.interval_variance),
        "damage_scale": float(schedule.damage_scale),
    }


def _barricade_schedule_payload(schedule: config.BarricadeSchedule) -> Dict[str, Any]:
    return {
        "base_interval": float(schedule.base_interval),
        "interval_variance": float(schedule.interval_variance),
        "reward_scale": float(schedule.reward_scale),
    }


def _resource_schedule_payload(schedule: config.ResourceSchedule) -> Dict[str, Any]:
    return {
        "base_interval": float(schedule.base_interval),
        "interval_variance": float(schedule.interval_variance),
        "amount_scale": float(schedule.amount_scale),
    }


def _weather_schedule_payload(schedule: config.WeatherSchedule) -> Dict[str, Any]:
    return {
        "base_interval": float(schedule.base_interval),
        "interval_variance": float(schedule.interval_variance),
        "duration_range": [float(value) for value in schedule.duration_range],
    }


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_")


__all__ = [
    "build_content_bundle",
    "glyph_synergy_weapon_payloads",
    "graveyard_biome_payload",
    "progression_payload",
    "relic_payloads",
    "launch_hunter_payloads",
]
