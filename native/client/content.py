"""DTO helpers for content payloads exported by the prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple


def _as_tuple(iterable: Any) -> Tuple[Any, ...]:
    if isinstance(iterable, tuple):
        return iterable
    if isinstance(iterable, list):
        return tuple(iterable)
    if isinstance(iterable, (str, bytes)):
        return (iterable,)
    if iterable is None:
        return tuple()
    return tuple(iterable)


def _string_tuple(iterable: Any) -> Tuple[str, ...]:
    return tuple(str(value) for value in _as_tuple(iterable))


@dataclass(frozen=True)
class EnemyDefinitionDTO:
    """Enemy blueprint replicated from the Python export."""

    id: str
    name: str
    category: str
    health: int
    damage: int
    speed: float
    lane: str
    behaviors: Tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EnemyDefinitionDTO":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            category=str(payload.get("category", "base")),
            health=int(payload.get("health", 0)),
            damage=int(payload.get("damage", 0)),
            speed=float(payload.get("speed", 0.0)),
            lane=str(payload.get("lane", "ground")),
            behaviors=_string_tuple(payload.get("behaviors", ())),
        )


@dataclass(frozen=True)
class MinibossDefinitionDTO(EnemyDefinitionDTO):
    """Miniboss blueprint with an unlock phase."""

    min_phase: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MinibossDefinitionDTO":
        base = EnemyDefinitionDTO.from_dict(payload)
        return cls(
            id=base.id,
            name=base.name,
            category=base.category,
            health=base.health,
            damage=base.damage,
            speed=base.speed,
            lane=base.lane,
            behaviors=base.behaviors,
            min_phase=int(payload.get("min_phase", 1)),
        )


@dataclass(frozen=True)
class SpawnScheduleDTO:
    base_interval: float
    interval_decay: float
    max_density: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SpawnScheduleDTO":
        return cls(
            base_interval=float(payload.get("base_interval", 0.0)),
            interval_decay=float(payload.get("interval_decay", 0.0)),
            max_density=int(payload.get("max_density", 0)),
        )


@dataclass(frozen=True)
class WaveScalingDTO:
    base_enemy_count: int
    per_wave_increment: int
    phase_multiplier: float
    per_wave_multiplier: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WaveScalingDTO":
        return cls(
            base_enemy_count=int(payload.get("base_enemy_count", 0)),
            per_wave_increment=int(payload.get("per_wave_increment", 0)),
            phase_multiplier=float(payload.get("phase_multiplier", 1.0)),
            per_wave_multiplier=float(payload.get("per_wave_multiplier", 0.0)),
        )


@dataclass(frozen=True)
class EliteBalanceDTO:
    spawn_chance: float
    scale_multiplier: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EliteBalanceDTO":
        return cls(
            spawn_chance=float(payload.get("spawn_chance", 0.0)),
            scale_multiplier=float(payload.get("scale_multiplier", 1.0)),
        )


@dataclass(frozen=True)
class PhaseBalanceDTO:
    spawn_schedule: SpawnScheduleDTO
    wave_scaling: WaveScalingDTO
    elite: EliteBalanceDTO

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PhaseBalanceDTO":
        spawn = SpawnScheduleDTO.from_dict(payload.get("spawn_schedule", {}))
        wave = WaveScalingDTO.from_dict(payload.get("wave_scaling", {}))
        elite = EliteBalanceDTO.from_dict(payload.get("elite", {}))
        return cls(spawn_schedule=spawn, wave_scaling=wave, elite=elite)


@dataclass(frozen=True)
class PhaseDefinitionDTO:
    id: str
    phase: int
    balance: PhaseBalanceDTO
    enemy_roster: Tuple[EnemyDefinitionDTO, ...]
    elite_roster: Tuple[EnemyDefinitionDTO, ...]
    minibosses: Tuple[MinibossDefinitionDTO, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PhaseDefinitionDTO":
        enemy_payload = payload.get("enemy_roster", [])
        elite_payload = payload.get("elite_roster", [])
        miniboss_payload = payload.get("minibosses", [])
        return cls(
            id=str(payload.get("id", "")),
            phase=int(payload.get("phase", 1)),
            balance=PhaseBalanceDTO.from_dict(payload.get("balance", {})),
            enemy_roster=tuple(EnemyDefinitionDTO.from_dict(entry) for entry in enemy_payload),
            elite_roster=tuple(EnemyDefinitionDTO.from_dict(entry) for entry in elite_payload),
            minibosses=tuple(MinibossDefinitionDTO.from_dict(entry) for entry in miniboss_payload),
        )


@dataclass(frozen=True)
class BossPhaseDTO:
    index: int
    health: int
    damage: int
    speed: float
    lane: str
    behaviors: Tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BossPhaseDTO":
        return cls(
            index=int(payload.get("index", 0)),
            health=int(payload.get("health", 0)),
            damage=int(payload.get("damage", 0)),
            speed=float(payload.get("speed", 0.0)),
            lane=str(payload.get("lane", "ground")),
            behaviors=_string_tuple(payload.get("behaviors", ())),
        )


@dataclass(frozen=True)
class FinalBossDTO:
    id: str
    name: str
    phases: Tuple[BossPhaseDTO, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FinalBossDTO":
        phases_payload = payload.get("phases", [])
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            phases=tuple(BossPhaseDTO.from_dict(entry) for entry in phases_payload),
        )


@dataclass(frozen=True)
class HazardBlueprintDTO:
    id: str
    name: str
    description: str
    base_damage: int
    slow: float
    duration: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HazardBlueprintDTO":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            base_damage=int(payload.get("base_damage", 0)),
            slow=float(payload.get("slow", 0.0)),
            duration=float(payload.get("duration", 0.0)),
        )


@dataclass(frozen=True)
class BarricadeBlueprintDTO:
    id: str
    name: str
    description: str
    durability: int
    salvage_reward: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BarricadeBlueprintDTO":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            durability=int(payload.get("durability", 0)),
            salvage_reward=int(payload.get("salvage_reward", 0)),
        )


@dataclass(frozen=True)
class ResourceCacheDTO:
    id: str
    name: str
    description: str
    base_amount: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResourceCacheDTO":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            base_amount=int(payload.get("base_amount", 0)),
        )


@dataclass(frozen=True)
class WeatherPatternDTO:
    id: str
    name: str
    description: str
    movement_modifier: float
    vision_modifier: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WeatherPatternDTO":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            movement_modifier=float(payload.get("movement_modifier", 0.0)),
            vision_modifier=float(payload.get("vision_modifier", 0.0)),
        )


@dataclass(frozen=True)
class HazardScheduleDTO:
    base_interval: float
    interval_variance: float
    damage_scale: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HazardScheduleDTO":
        return cls(
            base_interval=float(payload.get("base_interval", 0.0)),
            interval_variance=float(payload.get("interval_variance", 0.0)),
            damage_scale=float(payload.get("damage_scale", 0.0)),
        )


@dataclass(frozen=True)
class BarricadeScheduleDTO:
    base_interval: float
    interval_variance: float
    reward_scale: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BarricadeScheduleDTO":
        return cls(
            base_interval=float(payload.get("base_interval", 0.0)),
            interval_variance=float(payload.get("interval_variance", 0.0)),
            reward_scale=float(payload.get("reward_scale", 0.0)),
        )


@dataclass(frozen=True)
class ResourceScheduleDTO:
    base_interval: float
    interval_variance: float
    amount_scale: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResourceScheduleDTO":
        return cls(
            base_interval=float(payload.get("base_interval", 0.0)),
            interval_variance=float(payload.get("interval_variance", 0.0)),
            amount_scale=float(payload.get("amount_scale", 0.0)),
        )


@dataclass(frozen=True)
class WeatherScheduleDTO:
    base_interval: float
    interval_variance: float
    duration_range: Tuple[float, float]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WeatherScheduleDTO":
        duration_payload = payload.get("duration_range", (0.0, 0.0))
        return cls(
            base_interval=float(payload.get("base_interval", 0.0)),
            interval_variance=float(payload.get("interval_variance", 0.0)),
            duration_range=(
                float(duration_payload[0]),
                float(duration_payload[1]) if len(duration_payload) > 1 else float(duration_payload[0]),
            ),
        )


@dataclass(frozen=True)
class EnvironmentSchedulesDTO:
    hazard: HazardScheduleDTO
    barricade: BarricadeScheduleDTO
    resource: ResourceScheduleDTO
    weather: WeatherScheduleDTO

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EnvironmentSchedulesDTO":
        return cls(
            hazard=HazardScheduleDTO.from_dict(payload.get("hazard", {})),
            barricade=BarricadeScheduleDTO.from_dict(payload.get("barricade", {})),
            resource=ResourceScheduleDTO.from_dict(payload.get("resource", {})),
            weather=WeatherScheduleDTO.from_dict(payload.get("weather", {})),
        )


@dataclass(frozen=True)
class EnvironmentPhaseDTO:
    phase: int
    biome: str
    hazards: Tuple[HazardBlueprintDTO, ...]
    barricades: Tuple[BarricadeBlueprintDTO, ...]
    resource_caches: Tuple[ResourceCacheDTO, ...]
    weather_patterns: Tuple[WeatherPatternDTO, ...]
    schedules: EnvironmentSchedulesDTO

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EnvironmentPhaseDTO":
        return cls(
            phase=int(payload.get("phase", 0)),
            biome=str(payload.get("biome", "")),
            hazards=tuple(HazardBlueprintDTO.from_dict(entry) for entry in payload.get("hazards", [])),
            barricades=tuple(
                BarricadeBlueprintDTO.from_dict(entry) for entry in payload.get("barricades", [])
            ),
            resource_caches=tuple(
                ResourceCacheDTO.from_dict(entry) for entry in payload.get("resource_caches", [])
            ),
            weather_patterns=tuple(
                WeatherPatternDTO.from_dict(entry) for entry in payload.get("weather_patterns", [])
            ),
            schedules=EnvironmentSchedulesDTO.from_dict(payload.get("schedules", {})),
        )


@dataclass(frozen=True)
class BiomeContentDTO:
    id: str
    name: str
    description: str
    phases: Tuple[PhaseDefinitionDTO, ...]
    environment: Tuple[EnvironmentPhaseDTO, ...]
    final_boss: FinalBossDTO | None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BiomeContentDTO":
        phases_payload = payload.get("phases", [])
        boss_payload = payload.get("final_boss")
        environment_payload = payload.get("environment", [])
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            phases=tuple(PhaseDefinitionDTO.from_dict(entry) for entry in phases_payload),
            environment=tuple(EnvironmentPhaseDTO.from_dict(entry) for entry in environment_payload),
            final_boss=FinalBossDTO.from_dict(boss_payload) if boss_payload else None,
        )


@dataclass(frozen=True)
class HunterDTO:
    id: str
    name: str
    description: str
    max_health: int
    starting_weapon: str
    starting_weapon_tier: int
    signature_glyph: str | None
    starting_glyphs: Tuple[str, ...]
    abilities: "HunterAbilitiesDTO"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HunterDTO":
        glyph = payload.get("signature_glyph")
        glyphs_payload = payload.get("starting_glyphs", [])
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            max_health=int(payload.get("max_health", 0)),
            starting_weapon=str(payload.get("starting_weapon", "")),
            starting_weapon_tier=int(payload.get("starting_weapon_tier", 1)),
            signature_glyph=str(glyph) if glyph not in (None, "") else None,
            starting_glyphs=_string_tuple(glyphs_payload),
            abilities=HunterAbilitiesDTO.from_dict(payload.get("abilities", {})),
        )


@dataclass(frozen=True)
class DashAbilityDTO:
    cooldown: float
    strength: float

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DashAbilityDTO":
        return cls(
            cooldown=float(payload.get("cooldown", 0.0)),
            strength=float(payload.get("strength", 0.0)),
        )


@dataclass(frozen=True)
class HunterAbilitiesDTO:
    dash: DashAbilityDTO | None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HunterAbilitiesDTO":
        dash_payload = payload.get("dash")
        return cls(dash=DashAbilityDTO.from_dict(dash_payload) if dash_payload else None)


@dataclass(frozen=True)
class WeaponTierDTO:
    tier: int
    damage: float
    cooldown: float
    projectiles: int
    description: str | None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WeaponTierDTO":
        description = payload.get("description")
        return cls(
            tier=int(payload.get("tier", 1)),
            damage=float(payload.get("damage", 0.0)),
            cooldown=float(payload.get("cooldown", 0.0)),
            projectiles=int(payload.get("projectiles", 0)),
            description=str(description) if description not in (None, "") else None,
        )


@dataclass(frozen=True)
class WeaponDefinitionDTO:
    id: str
    name: str
    glyph_synergy: str
    role: str
    description: str
    ultimate: str | None
    tiers: Tuple[WeaponTierDTO, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WeaponDefinitionDTO":
        tiers_payload = payload.get("tiers", [])
        ultimate = payload.get("ultimate")
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            glyph_synergy=str(payload.get("glyph_synergy", "")),
            role=str(payload.get("role", "")),
            description=str(payload.get("description", "")),
            ultimate=str(ultimate) if ultimate not in (None, "") else None,
            tiers=tuple(WeaponTierDTO.from_dict(entry) for entry in tiers_payload),
        )


@dataclass(frozen=True)
class RelicModifierDTO:
    max_health: int
    damage_scale: float
    defense_scale: float
    hazard_resist: float
    salvage_scale: float
    soul_scale: float
    lifesteal_bonus: float
    regen_per_second: float
    glyph_bonus: Dict[str, int]
    salvage_bonus_flat: int
    heal_on_pickup: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RelicModifierDTO":
        glyph_payload = payload.get("glyph_bonus", {})
        if isinstance(glyph_payload, Mapping):
            glyph_bonus = {str(key): int(value) for key, value in glyph_payload.items()}
        else:
            glyph_bonus = {}
        return cls(
            max_health=int(payload.get("max_health", 0)),
            damage_scale=float(payload.get("damage_scale", 0.0)),
            defense_scale=float(payload.get("defense_scale", 0.0)),
            hazard_resist=float(payload.get("hazard_resist", 0.0)),
            salvage_scale=float(payload.get("salvage_scale", 0.0)),
            soul_scale=float(payload.get("soul_scale", 0.0)),
            lifesteal_bonus=float(payload.get("lifesteal_bonus", 0.0)),
            regen_per_second=float(payload.get("regen_per_second", 0.0)),
            glyph_bonus=glyph_bonus,
            salvage_bonus_flat=int(payload.get("salvage_bonus_flat", 0)),
            heal_on_pickup=int(payload.get("heal_on_pickup", 0)),
        )


@dataclass(frozen=True)
class RelicDefinitionDTO:
    id: str
    name: str
    description: str
    modifier: RelicModifierDTO

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RelicDefinitionDTO":
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            modifier=RelicModifierDTO.from_dict(payload.get("modifier", {})),
        )


@dataclass(frozen=True)
class ProgressionSettingsDTO:
    glyph_set_size: int
    max_upgrade_options: int
    run_duration_seconds: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProgressionSettingsDTO":
        return cls(
            glyph_set_size=int(payload.get("glyph_set_size", 0)),
            max_upgrade_options=int(payload.get("max_upgrade_options", 0)),
            run_duration_seconds=int(payload.get("run_duration_seconds", 0)),
        )


@dataclass(frozen=True)
class ContentBundleDTO:
    version: str
    biomes: Tuple[BiomeContentDTO, ...]
    hunters: Tuple[HunterDTO, ...]
    weapons: Tuple[WeaponDefinitionDTO, ...]
    relics: Tuple[RelicDefinitionDTO, ...]
    progression: ProgressionSettingsDTO

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContentBundleDTO":
        return cls(
            version=str(payload.get("version", "")),
            biomes=tuple(BiomeContentDTO.from_dict(entry) for entry in payload.get("biomes", [])),
            hunters=tuple(HunterDTO.from_dict(entry) for entry in payload.get("hunters", [])),
            weapons=tuple(WeaponDefinitionDTO.from_dict(entry) for entry in payload.get("weapons", [])),
            relics=tuple(RelicDefinitionDTO.from_dict(entry) for entry in payload.get("relics", [])),
            progression=ProgressionSettingsDTO.from_dict(payload.get("progression", {})),
        )


__all__ = [
    "BiomeContentDTO",
    "BarricadeBlueprintDTO",
    "BarricadeScheduleDTO",
    "BossPhaseDTO",
    "ContentBundleDTO",
    "DashAbilityDTO",
    "EnemyDefinitionDTO",
    "EnvironmentPhaseDTO",
    "EnvironmentSchedulesDTO",
    "FinalBossDTO",
    "HazardBlueprintDTO",
    "HazardScheduleDTO",
    "HunterDTO",
    "HunterAbilitiesDTO",
    "MinibossDefinitionDTO",
    "PhaseBalanceDTO",
    "PhaseDefinitionDTO",
    "ProgressionSettingsDTO",
    "RelicDefinitionDTO",
    "RelicModifierDTO",
    "ResourceCacheDTO",
    "ResourceScheduleDTO",
    "SpawnScheduleDTO",
    "WeaponDefinitionDTO",
    "WeaponTierDTO",
    "WeatherPatternDTO",
    "WeatherScheduleDTO",
]
