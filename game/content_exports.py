"""Structured content exports consumed by the native runtime importer."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from . import combat, config, content
from .entities import EnemyLane, GlyphFamily
from .game_state import weapon_upgrade_paths
from .profile import default_hunters

_LAUNCH_HUNTERS: Sequence[str] = ("hunter_varik", "hunter_mira")

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
        "biomes": [graveyard_biome_payload()],
        "hunters": launch_hunter_payloads(),
        "weapons": glyph_synergy_weapon_payloads(),
    }


def graveyard_biome_payload() -> Dict[str, Any]:
    """Generate the encounter payload for the Graveyard biome."""

    phases: List[Dict[str, Any]] = []
    enemy_catalog = content.enemy_blueprints(include_elites=True)
    miniboss_entries = content.miniboss_blueprints()

    for phase in range(1, 5):
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
        "final_boss": boss,
    }


def launch_hunter_payloads() -> List[Dict[str, Any]]:
    """Return the hunter roster earmarked for the vertical slice."""

    roster = default_hunters()
    payload: List[Dict[str, Any]] = []
    for hunter_id in _LAUNCH_HUNTERS:
        definition = roster[hunter_id]
        payload.append(
            {
                "id": definition.id,
                "name": definition.name,
                "description": definition.description,
                "max_health": int(definition.max_health),
                "starting_weapon": definition.starting_weapon,
                "starting_weapon_tier": int(definition.starting_weapon_tier),
                "signature_glyph": definition.signature_glyph.value if definition.signature_glyph else None,
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


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_")


__all__ = [
    "build_content_bundle",
    "glyph_synergy_weapon_payloads",
    "graveyard_biome_payload",
    "launch_hunter_payloads",
]
