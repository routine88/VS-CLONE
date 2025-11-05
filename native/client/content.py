"""DTO helpers for content payloads exported by the prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple


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
class BiomeContentDTO:
    id: str
    name: str
    description: str
    phases: Tuple[PhaseDefinitionDTO, ...]
    final_boss: FinalBossDTO | None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BiomeContentDTO":
        phases_payload = payload.get("phases", [])
        boss_payload = payload.get("final_boss")
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            phases=tuple(PhaseDefinitionDTO.from_dict(entry) for entry in phases_payload),
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

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HunterDTO":
        glyph = payload.get("signature_glyph")
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            max_health=int(payload.get("max_health", 0)),
            starting_weapon=str(payload.get("starting_weapon", "")),
            starting_weapon_tier=int(payload.get("starting_weapon_tier", 1)),
            signature_glyph=str(glyph) if glyph not in (None, "") else None,
        )


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
class ContentBundleDTO:
    version: str
    biomes: Tuple[BiomeContentDTO, ...]
    hunters: Tuple[HunterDTO, ...]
    weapons: Tuple[WeaponDefinitionDTO, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContentBundleDTO":
        return cls(
            version=str(payload.get("version", "")),
            biomes=tuple(BiomeContentDTO.from_dict(entry) for entry in payload.get("biomes", [])),
            hunters=tuple(HunterDTO.from_dict(entry) for entry in payload.get("hunters", [])),
            weapons=tuple(WeaponDefinitionDTO.from_dict(entry) for entry in payload.get("weapons", [])),
        )


__all__ = [
    "BiomeContentDTO",
    "BossPhaseDTO",
    "ContentBundleDTO",
    "EnemyDefinitionDTO",
    "FinalBossDTO",
    "HunterDTO",
    "MinibossDefinitionDTO",
    "PhaseBalanceDTO",
    "PhaseDefinitionDTO",
    "SpawnScheduleDTO",
    "WeaponDefinitionDTO",
    "WeaponTierDTO",
]
