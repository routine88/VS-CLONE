"""Player profile and loadout helpers bridging meta progression to runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, TYPE_CHECKING

from .entities import GlyphFamily, Player, UpgradeCard, UpgradeType
from .game_state import GameState, default_upgrade_cards
from .meta import MetaProgressionSystem, SigilLedger, Unlockable
from .session import RunResult
from .systems import UpgradeDeck

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from .monetization import CosmeticInventory


@dataclass(frozen=True)
class HunterDefinition:
    """Describes a hunter archetype available to the player profile."""

    id: str
    name: str
    description: str
    max_health: int
    starting_weapon: str
    starting_weapon_tier: int
    signature_glyph: Optional[GlyphFamily] = None


def default_hunters() -> Dict[str, HunterDefinition]:
    """Return the base hunter roster outlined by the PRD."""

    return {
        "hunter_varik": HunterDefinition(
            id="hunter_varik",
            name="Varik the Nightblade",
            description="Balanced starter wielding the Dusk Repeater.",
            max_health=120,
            starting_weapon="Dusk Repeater",
            starting_weapon_tier=1,
            signature_glyph=GlyphFamily.BLOOD,
        ),
        "hunter_mira": HunterDefinition(
            id="hunter_mira",
            name="Mira the Stormcaller",
            description="Starter hunter specializing in chaining lightning.",
            max_health=105,
            starting_weapon="Storm Siphon",
            starting_weapon_tier=1,
            signature_glyph=GlyphFamily.STORM,
        ),
        "hunter_lunara": HunterDefinition(
            id="hunter_lunara",
            name="Lunara the Moonshadow",
            description="Unlockable aerial acrobat with evasive tools.",
            max_health=95,
            starting_weapon="Gloom Chakram",
            starting_weapon_tier=1,
            signature_glyph=GlyphFamily.CLOCKWORK,
        ),
        "hunter_aurora": HunterDefinition(
            id="hunter_aurora",
            name="Aurora the Dawnbringer",
            description="Unlockable support weaving radiant slows and shields.",
            max_health=130,
            starting_weapon="Nocturne Harp",
            starting_weapon_tier=1,
            signature_glyph=GlyphFamily.VERDANT,
        ),
    }


_UNLOCK_GLYPH_MAP = {
    "glyph_verdant": GlyphFamily.VERDANT,
}

_UNLOCK_WEAPON_CARDS = {
    "weapon_nocturne": "Nocturne Harp",
}


class PlayerProfile:
    """Represents persistent player progression and preferred loadouts."""

    def __init__(
        self,
        *,
        hunters: Optional[Dict[str, HunterDefinition]] = None,
        meta: Optional[MetaProgressionSystem] = None,
        owned_hunters: Optional[Iterable[str]] = None,
        weapon_cards: Optional[Iterable[str]] = None,
        glyph_families: Optional[Iterable[GlyphFamily]] = None,
        cosmetic_inventory: Optional["CosmeticInventory"] = None,
    ) -> None:
        roster = hunters or default_hunters()
        if not roster:
            raise ValueError("at least one hunter definition is required")
        self._hunters: Dict[str, HunterDefinition] = roster

        base_hunters = set(owned_hunters) if owned_hunters is not None else {"hunter_varik", "hunter_mira"}
        self.owned_hunters: Set[str] = {hid for hid in base_hunters if hid in roster}
        if not self.owned_hunters:
            raise ValueError("owned_hunters must contain at least one valid hunter")

        self.active_hunter: str = next(iter(sorted(self.owned_hunters)))

        base_weapon_cards = set(weapon_cards) if weapon_cards is not None else {
            "Dusk Repeater",
            "Gloom Chakram",
            "Storm Siphon",
            "Bloodthorn Lance",
            "Gravebloom Staff",
            "Tempest Gauntlet",
            "Frostbrand Edge",
            "Inferno Lantern",
            "Umbral Coil",
        }
        self.available_weapon_cards: Set[str] = set(base_weapon_cards)

        base_glyphs = set(glyph_families) if glyph_families is not None else {
            GlyphFamily.BLOOD,
            GlyphFamily.STORM,
            GlyphFamily.FROST,
            GlyphFamily.INFERNO,
            GlyphFamily.CLOCKWORK,
        }
        self.available_glyph_families: Set[GlyphFamily] = set(base_glyphs)

        self.meta = meta or MetaProgressionSystem()

        if cosmetic_inventory is None:
            from .monetization import CosmeticInventory

            self.cosmetics = CosmeticInventory()
        else:
            self.cosmetics = cosmetic_inventory

    @property
    def hunters(self) -> Dict[str, HunterDefinition]:
        return self._hunters

    @property
    def ledger(self) -> SigilLedger:
        return self.meta.ledger

    def set_active_hunter(self, hunter_id: str) -> None:
        if hunter_id not in self.owned_hunters:
            raise ValueError(f"hunter '{hunter_id}' is not unlocked")
        self.active_hunter = hunter_id

    def available_upgrade_cards(self) -> List[UpgradeCard]:
        cards: List[UpgradeCard] = []
        for card in default_upgrade_cards():
            if card.type is UpgradeType.GLYPH and card.glyph_family not in self.available_glyph_families:
                continue
            if card.type is UpgradeType.WEAPON and card.name not in self.available_weapon_cards:
                continue
            cards.append(card)
        if not cards:
            raise ValueError("profile has no upgrade cards available")
        return cards

    def start_run(self) -> GameState:
        hunter = self._hunters[self.active_hunter]
        player = Player()
        player.max_health = hunter.max_health
        player.health = hunter.max_health
        player.unlocked_weapons = {hunter.starting_weapon: hunter.starting_weapon_tier}
        if "Dusk Repeater" not in player.unlocked_weapons:
            player.unlocked_weapons["Dusk Repeater"] = 1
        if hunter.signature_glyph and hunter.signature_glyph in self.available_glyph_families:
            player.add_glyph(hunter.signature_glyph)
        deck = UpgradeDeck(self.available_upgrade_cards())
        return GameState(player=player, upgrade_deck=deck)

    def record_run(self, result: RunResult) -> int:
        return self.meta.record_run(result)

    def claim_unlock(self, unlock_id: str, *, run_result: Optional[RunResult] = None) -> Unlockable:
        if run_result is not None:
            available = {unlock.id for unlock in self.meta.available_unlocks(run_result=run_result)}
            if unlock_id not in available:
                raise ValueError(f"unlock '{unlock_id}' does not meet requirements for the supplied run")
        unlock = self.meta.unlock(unlock_id)
        self.apply_unlock(unlock)
        return unlock

    def apply_unlock(self, unlock: Unlockable) -> None:
        if unlock.category == "hunter":
            if unlock.id not in self._hunters:
                raise ValueError(f"unknown hunter '{unlock.id}' for unlock")
            self.owned_hunters.add(unlock.id)
        elif unlock.category == "weapon":
            card_name = _UNLOCK_WEAPON_CARDS.get(unlock.id, unlock.name)
            self.available_weapon_cards.add(card_name)
        elif unlock.category == "glyph":
            family = _UNLOCK_GLYPH_MAP.get(unlock.id)
            if family is None:
                raise ValueError(f"unlock '{unlock.id}' missing glyph mapping")
            self.available_glyph_families.add(family)
        else:
            raise ValueError(f"unsupported unlock category '{unlock.category}'")

        if self.active_hunter not in self.owned_hunters:
            self.active_hunter = next(iter(sorted(self.owned_hunters)))

    def unlocked_hunters(self) -> Sequence[HunterDefinition]:
        return [self._hunters[hid] for hid in sorted(self.owned_hunters)]


__all__ = [
    "HunterDefinition",
    "PlayerProfile",
    "default_hunters",
]
