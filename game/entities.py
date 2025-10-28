"""Entity and upgrade model definitions for the prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Literal, Optional


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


@dataclass
class Enemy:
    """Represents an enemy spawn entry."""

    name: str
    health: int
    damage: int
    speed: float


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

