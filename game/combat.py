"""Combat resolution utilities for the Nightfall Survivors prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal, Mapping

from .entities import Enemy, GlyphFamily, Player, WaveDescriptor


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
            expected_damage = pressure * (duration / (duration + mitigation))
            damage_taken = int(expected_damage)

            total_health += phase_health
            total_duration += duration
            total_damage_taken += damage_taken
            notes.append(
                f"Phase {index} endured {duration:.1f}s with pressure {pressure:.1f}, costing approximately {damage_taken} health."
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

