"""Combat resolution utilities for the Nightfall Survivors prototype."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Literal, Mapping

from .entities import Enemy, EnemyLane, GlyphFamily, Player, WaveDescriptor


@dataclass(frozen=True)
class WeaponTier:
    """Represents the stats for a particular weapon tier."""

    damage: float
    cooldown: float
    projectiles: int = 1

    @property
    def dps(self) -> float:
        if self.cooldown <= 0:
            raise ValueError("weapon cooldown must be positive")
        return (self.damage * self.projectiles) / self.cooldown


WeaponLibrary = Mapping[str, Mapping[int, WeaponTier]]


_WEAPON_LIBRARY: WeaponLibrary = {
    "Dusk Repeater": {
        1: WeaponTier(damage=18, cooldown=0.9, projectiles=1),
        2: WeaponTier(damage=22, cooldown=0.85, projectiles=2),
        3: WeaponTier(damage=28, cooldown=0.8, projectiles=2),
        4: WeaponTier(damage=34, cooldown=0.75, projectiles=3),
    },
    "Gloom Chakram": {
        1: WeaponTier(damage=26, cooldown=1.2, projectiles=1),
        2: WeaponTier(damage=32, cooldown=1.1, projectiles=2),
        3: WeaponTier(damage=40, cooldown=1.0, projectiles=2),
        4: WeaponTier(damage=50, cooldown=0.9, projectiles=3),
    },
    "Storm Siphon": {
        1: WeaponTier(damage=14, cooldown=0.6, projectiles=1),
        2: WeaponTier(damage=17, cooldown=0.55, projectiles=2),
        3: WeaponTier(damage=21, cooldown=0.5, projectiles=3),
        4: WeaponTier(damage=26, cooldown=0.45, projectiles=4),
    },
    "Nocturne Harp": {
        1: WeaponTier(damage=24, cooldown=1.4, projectiles=1),
        2: WeaponTier(damage=30, cooldown=1.25, projectiles=2),
        3: WeaponTier(damage=38, cooldown=1.1, projectiles=2),
        4: WeaponTier(damage=48, cooldown=1.0, projectiles=3),
    },
    "Bloodthorn Lance": {
        1: WeaponTier(damage=36, cooldown=1.5, projectiles=1),
        2: WeaponTier(damage=44, cooldown=1.35, projectiles=1),
        3: WeaponTier(damage=56, cooldown=1.2, projectiles=1),
        4: WeaponTier(damage=72, cooldown=1.05, projectiles=1),
    },
    "Gravebloom Staff": {
        1: WeaponTier(damage=20, cooldown=1.3, projectiles=2),
        2: WeaponTier(damage=26, cooldown=1.2, projectiles=3),
        3: WeaponTier(damage=32, cooldown=1.1, projectiles=3),
        4: WeaponTier(damage=40, cooldown=1.0, projectiles=4),
    },
    "Tempest Gauntlet": {
        1: WeaponTier(damage=16, cooldown=0.7, projectiles=1),
        2: WeaponTier(damage=20, cooldown=0.65, projectiles=2),
        3: WeaponTier(damage=25, cooldown=0.6, projectiles=3),
        4: WeaponTier(damage=32, cooldown=0.55, projectiles=3),
    },
    "Frostbrand Edge": {
        1: WeaponTier(damage=28, cooldown=1.1, projectiles=1),
        2: WeaponTier(damage=34, cooldown=1.0, projectiles=1),
        3: WeaponTier(damage=42, cooldown=0.95, projectiles=2),
        4: WeaponTier(damage=52, cooldown=0.9, projectiles=2),
    },
    "Inferno Lantern": {
        1: WeaponTier(damage=18, cooldown=1.6, projectiles=3),
        2: WeaponTier(damage=24, cooldown=1.45, projectiles=3),
        3: WeaponTier(damage=30, cooldown=1.3, projectiles=4),
        4: WeaponTier(damage=38, cooldown=1.15, projectiles=4),
    },
    "Umbral Coil": {
        1: WeaponTier(damage=22, cooldown=1.0, projectiles=1),
        2: WeaponTier(damage=28, cooldown=0.95, projectiles=2),
        3: WeaponTier(damage=34, cooldown=0.9, projectiles=3),
        4: WeaponTier(damage=42, cooldown=0.85, projectiles=3),
    },
}


def weapon_tier(weapon: str, tier: int) -> WeaponTier | None:
    """Return the :class:`WeaponTier` stats for the supplied weapon/tier."""

    return _WEAPON_LIBRARY.get(weapon, {}).get(tier)


def weapon_library() -> WeaponLibrary:
    """Expose the full weapon library for downstream systems."""

    return _WEAPON_LIBRARY


def glyph_damage_multiplier(player: Player) -> float:
    """Return the damage multiplier applied from glyph ownership."""

    return _glyph_damage_multiplier(player)


@dataclass(frozen=True)
class CombatSummary:
    """Outcome of a resolved encounter."""

    kind: Literal["wave", "miniboss", "final_boss"]
    enemies_defeated: int
    souls_gained: int
    damage_taken: int
    healing_received: int
    duration: float
    notes: List[str]


def _weapon_dps(player: Player) -> float:
    total = 0.0
    for weapon, tier in player.unlocked_weapons.items():
        tier_stats = _WEAPON_LIBRARY.get(weapon, {}).get(tier)
        if tier_stats is None:
            continue
        total += tier_stats.dps
    # Apply a light level scaling so leveling feels impactful.
    level_bonus = 1.0 + 0.04 * max(0, player.level - 1)
    return total * level_bonus


def _glyph_damage_multiplier(player: Player) -> float:
    storm_bonus = 0.06 * player.glyph_counts[GlyphFamily.STORM]
    inferno_bonus = 0.05 * player.glyph_counts[GlyphFamily.INFERNO]
    verdant_bonus = 0.02 * player.glyph_counts[GlyphFamily.VERDANT]
    return 1.0 + storm_bonus + inferno_bonus + verdant_bonus


def _defense_factor(player: Player) -> float:
    frost_bonus = 0.08 * player.glyph_counts[GlyphFamily.FROST]
    clockwork_bonus = 0.04 * player.glyph_counts[GlyphFamily.CLOCKWORK]
    base = 1.0 + frost_bonus + clockwork_bonus
    # Survival upgrades add to max health which indirectly improves endurance;
    # reflect that by scaling with remaining health ratio.
    endurance = player.health / max(1, player.max_health)
    return base + 0.5 * endurance


def _lifesteal_ratio(player: Player) -> float:
    sets_completed = player.glyph_sets_awarded[GlyphFamily.BLOOD]
    glyph_bonus = 0.01 * player.glyph_counts[GlyphFamily.BLOOD]
    return 0.03 * sets_completed + glyph_bonus


def _souls_from_enemies(enemies: Iterable[Enemy]) -> int:
    total_health = sum(enemy.health for enemy in enemies)
    return max(5, int(total_health * 0.35))


_BEHAVIOR_PRESSURE: Mapping[str, float] = {
    "ranged": 0.12,
    "kamikaze": 0.2,
    "clinger": 0.16,
    "dash": 0.1,
    "pounce": 0.1,
    "shockwave": 0.14,
    "wail": 0.08,
    "slow": 0.05,
    "shield": 0.06,
    "stagger": 0.04,
    "burrow": 0.05,
    "swoop": 0.06,
}


def _lane_pressure_multiplier(enemies: Iterable[Enemy]) -> float:
    counts: Counter[EnemyLane] = Counter(enemy.lane for enemy in enemies)
    multiplier = 1.0
    if counts[EnemyLane.AIR]:
        multiplier += 0.05 * counts[EnemyLane.AIR]
    if counts[EnemyLane.CEILING]:
        multiplier += 0.1 + 0.03 * max(0, counts[EnemyLane.CEILING] - 1)
    return multiplier


def _behavior_pressure_multiplier(enemies: Iterable[Enemy]) -> float:
    total_bonus = 0.0
    enemy_count = 0
    for enemy in enemies:
        enemy_count += 1
        for tag in enemy.behaviors:
            total_bonus += _BEHAVIOR_PRESSURE.get(tag, 0.0)
    if enemy_count == 0:
        return 1.0
    averaged = total_bonus / enemy_count
    return max(0.8, 1.0 + averaged)


class CombatResolver:
    """Resolves encounters into high level combat summaries."""

    def resolve_wave(self, player: Player, wave: WaveDescriptor) -> CombatSummary:
        return self._resolve(player, wave.enemies, kind="wave")

    def resolve_miniboss(self, player: Player, enemy: Enemy) -> CombatSummary:
        return self._resolve(player, [enemy], kind="miniboss")

    def resolve_final_boss(self, player: Player, phases: Iterable[Enemy]) -> CombatSummary:
        enemy_list = list(phases)
        if not enemy_list:
            raise ValueError("final boss requires at least one phase")

        player_dps = max(1.0, _weapon_dps(player) * _glyph_damage_multiplier(player))
        mitigation = _defense_factor(player)
        lifesteal_ratio = _lifesteal_ratio(player)

        total_health = 0
        total_damage_taken = 0
        total_duration = 0.0
        notes: List[str] = []

        for index, phase in enumerate(enemy_list, start=1):
            phase_health = phase.health
            duration = phase_health / player_dps
            pressure = phase.damage * (1.25 + 0.12 * phase.speed)
            lane_multiplier = _lane_pressure_multiplier([phase])
            behavior_multiplier = _behavior_pressure_multiplier([phase])
            pressure *= lane_multiplier * behavior_multiplier
            expected_damage = pressure * (duration / (duration + mitigation))
            damage_taken = int(expected_damage)

            total_health += phase_health
            total_duration += duration
            total_damage_taken += damage_taken
            notes.append(
                "Phase {index} endured {duration:.1f}s with pressure {pressure:.1f}, costing approximately {damage_taken} "
                "health while attacking from the {lane} lane.".format(
                    index=index,
                    duration=duration,
                    pressure=pressure,
                    damage_taken=damage_taken,
                    lane=phase.lane.value,
                )
            )

            if lane_multiplier != 1.0 or behavior_multiplier != 1.0:
                notes.append(
                    f"    Modifiers applied -> lane x{lane_multiplier:.2f}, behaviors x{behavior_multiplier:.2f}."
                )

        souls = max(50, int(total_health * 0.55))
        healing = int(total_health * lifesteal_ratio)
        missing_health = max(0, player.max_health - player.health)
        healing = min(healing, missing_health)

        if lifesteal_ratio > 0 and healing > 0:
            notes.append(f"Life steal during the duel restored {healing} health.")

        notes.append("The final blow scatters the Dawn Revenant's essence.")

        return CombatSummary(
            kind="final_boss",
            enemies_defeated=len(enemy_list),
            souls_gained=souls,
            damage_taken=total_damage_taken,
            healing_received=healing,
            duration=total_duration,
            notes=notes,
        )

    def _resolve(self, player: Player, enemies: Iterable[Enemy], kind: Literal["wave", "miniboss"]) -> CombatSummary:
        enemy_list = list(enemies)
        if not enemy_list:
            return CombatSummary(kind=kind, enemies_defeated=0, souls_gained=0, damage_taken=0, healing_received=0, duration=0.0, notes=["No enemies present."])

        total_health = sum(enemy.health for enemy in enemy_list)
        total_damage = sum(enemy.damage for enemy in enemy_list)
        total_speed = sum(enemy.speed for enemy in enemy_list)

        player_dps = max(1.0, _weapon_dps(player) * _glyph_damage_multiplier(player))
        duration = total_health / player_dps

        pressure = total_damage * (1.0 + 0.15 * total_speed)
        lane_multiplier = _lane_pressure_multiplier(enemy_list)
        behavior_multiplier = _behavior_pressure_multiplier(enemy_list)
        pressure *= lane_multiplier * behavior_multiplier
        mitigation = _defense_factor(player)
        expected_damage = pressure * (duration / (duration + mitigation))
        damage_taken = int(expected_damage)

        souls = _souls_from_enemies(enemy_list)

        lifesteal_ratio = _lifesteal_ratio(player)
        healing = int(total_health * lifesteal_ratio)
        missing_health = max(0, player.max_health - player.health)
        healing = min(healing, missing_health)

        notes = [
            f"Player DPS: {player_dps:.1f}",
            f"Encounter duration: {duration:.1f}s",
            f"Incoming pressure: {pressure:.1f}",
        ]

        if lane_multiplier != 1.0:
            notes.append(f"Lane modifier applied: x{lane_multiplier:.2f}")
        if behavior_multiplier != 1.0:
            notes.append(f"Behavior modifier applied: x{behavior_multiplier:.2f}")

        if lifesteal_ratio > 0:
            notes.append(f"Life steal restored {healing} health.")

        return CombatSummary(
            kind=kind,
            enemies_defeated=len(enemy_list),
            souls_gained=souls,
            damage_taken=damage_taken,
            healing_received=healing,
            duration=duration,
            notes=notes,
        )

