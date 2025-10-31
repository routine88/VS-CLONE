"""Entity and upgrade model definitions for the prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Literal, Optional, Tuple, TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover - imports used for typing only
    from .relics import RelicModifier


class GlyphFamily(str, Enum):
    BLOOD = "blood"
    STORM = "storm"
    CLOCKWORK = "clockwork"
    FROST = "frost"
    INFERNO = "inferno"
    VERDANT = "verdant"


class UpgradeType(Enum):
    WEAPON = auto()
    GLYPH = auto()
    SURVIVAL = auto()


class EnemyLane(str, Enum):
    """Spatial lane an enemy prefers when engaging the player."""

    GROUND = "ground"
    AIR = "air"
    CEILING = "ceiling"


@dataclass
class UpgradeCard:
    """Represents a single upgrade choice during a level-up."""

    name: str
    description: str
    type: UpgradeType
    glyph_family: Optional[GlyphFamily] = None
    weapon_tier: Optional[int] = None
    modifiers: Dict[str, float] = field(default_factory=dict)


def _glyph_dict(default: int = 0) -> Dict[GlyphFamily, int]:
    return {family: default for family in GlyphFamily}


@dataclass
class Player:
    """Simplified player state for the logic prototype."""

    max_health: int = 100
    health: int = 100
    level: int = 1
    experience: int = 0
    glyph_counts: Dict[GlyphFamily, int] = field(default_factory=_glyph_dict)
    glyph_sets_awarded: Dict[GlyphFamily, int] = field(default_factory=_glyph_dict)
    unlocked_weapons: Dict[str, int] = field(default_factory=lambda: {"Dusk Repeater": 1})
    relics: List[str] = field(default_factory=list)
    salvage: int = 0
    damage_multiplier: float = 1.0
    defense_multiplier: float = 1.0
    hazard_resistance: float = 0.0
    salvage_multiplier: float = 1.0
    soul_multiplier: float = 1.0
    lifesteal_bonus: float = 0.0
    regen_per_second: float = 0.0

    def add_glyph(self, family: GlyphFamily) -> None:
        """Increase glyph count for the given family."""

        self.glyph_counts[family] += 1

    def complete_glyph_sets(self) -> List[GlyphFamily]:
        """Return glyph families with newly completed sets and mark them as claimed."""

        from .config import GLYPH_SET_SIZE

        completed: List[GlyphFamily] = []
        for family, count in self.glyph_counts.items():
            sets_available = count // GLYPH_SET_SIZE
            sets_awarded = self.glyph_sets_awarded[family]
            while sets_awarded < sets_available:
                completed.append(family)
                sets_awarded += 1
            self.glyph_sets_awarded[family] = sets_awarded
        return completed

    def apply_upgrade(self, card: UpgradeCard) -> List[GlyphFamily]:
        """Apply a chosen upgrade to the player state and return completed glyph sets."""

        completed: List[GlyphFamily] = []
        if card.type is UpgradeType.GLYPH and card.glyph_family:
            self.add_glyph(card.glyph_family)
            completed = self.complete_glyph_sets()
        elif card.type is UpgradeType.WEAPON and card.weapon_tier:
            self.unlocked_weapons[card.name] = card.weapon_tier
        else:
            for stat, value in card.modifiers.items():
                if stat == "max_health":
                    increase = int(value)
                    self.max_health += increase
                    self.health += increase
                elif stat == "haste":
                    # Placeholder for future stat hooks.
                    pass
        return completed

    def add_salvage(self, amount: int) -> int:
        """Grant salvage resources collected from the environment."""

        if amount < 0:
            raise ValueError("salvage cannot be negative")
        scaled = amount
        if amount > 0 and self.salvage_multiplier != 1.0:
            scaled = max(1, int(round(amount * self.salvage_multiplier)))
        self.salvage += scaled
        return scaled

    def scale_soul_reward(self, amount: int) -> int:
        """Return the soul reward after applying run modifiers."""

        if amount <= 0:
            return amount
        if self.soul_multiplier == 1.0:
            return amount
        scaled = int(round(amount * self.soul_multiplier))
        return max(1, scaled)

    def apply_relic_modifier(self, modifier: "RelicModifier") -> List[GlyphFamily]:
        """Apply relic bonuses and return any glyph sets completed."""

        completed_sets: List[GlyphFamily] = []
        if modifier.max_health:
            self.max_health += modifier.max_health
            self.health += modifier.max_health
        if modifier.heal_on_pickup:
            self.health = min(self.max_health, self.health + modifier.heal_on_pickup)
        if modifier.damage_scale:
            self.damage_multiplier *= 1.0 + modifier.damage_scale
        if modifier.defense_scale:
            self.defense_multiplier *= 1.0 + modifier.defense_scale
        if modifier.hazard_resist:
            self.hazard_resistance = min(0.9, self.hazard_resistance + modifier.hazard_resist)
        if modifier.salvage_scale:
            self.salvage_multiplier *= 1.0 + modifier.salvage_scale
        if modifier.soul_scale:
            self.soul_multiplier *= 1.0 + modifier.soul_scale
        if modifier.lifesteal_bonus:
            self.lifesteal_bonus += modifier.lifesteal_bonus
        if modifier.regen_per_second:
            self.regen_per_second += modifier.regen_per_second
        if modifier.salvage_bonus_flat:
            bonus = max(0, int(modifier.salvage_bonus_flat))
            if bonus:
                self.salvage += bonus

        if modifier.glyph_bonus:
            for family, amount in modifier.glyph_bonus.items():
                for _ in range(max(0, int(amount))):
                    self.add_glyph(family)
            completed_sets.extend(self.complete_glyph_sets())

        self.health = min(self.max_health, max(0, self.health))
        return completed_sets


@dataclass
class Enemy:
    """Represents an enemy spawn entry."""

    name: str
    health: int
    damage: int
    speed: float
    lane: EnemyLane = EnemyLane.GROUND
    behaviors: Tuple[str, ...] = field(default_factory=tuple)


@dataclass
class WaveDescriptor:
    """Data container describing a wave of enemies."""

    phase: int
    wave_index: int
    enemies: List[Enemy]


@dataclass
class Encounter:
    """Represents the next combat beat delivered to the player."""

    kind: Literal["wave", "miniboss", "final_boss"]
    wave: Optional[WaveDescriptor] = None
    miniboss: Optional[Enemy] = None
    boss_phases: Optional[List[Enemy]] = None
    relic_reward: Optional[str] = None

