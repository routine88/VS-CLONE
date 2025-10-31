"""Relic definitions and effects for Nightfall Survivors runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence

from .entities import GlyphFamily


@dataclass(frozen=True)
class RelicModifier:
    """Numeric adjustments applied when a relic is claimed."""

    max_health: int = 0
    damage_scale: float = 0.0
    defense_scale: float = 0.0
    hazard_resist: float = 0.0
    salvage_scale: float = 0.0
    soul_scale: float = 0.0
    lifesteal_bonus: float = 0.0
    regen_per_second: float = 0.0
    glyph_bonus: Mapping[GlyphFamily, int] = field(default_factory=dict)
    salvage_bonus_flat: int = 0
    heal_on_pickup: int = 0


@dataclass(frozen=True)
class RelicDefinition:
    """Static metadata describing a relic and its modifier."""

    id: str
    name: str
    description: str
    modifier: RelicModifier


def _glyph_bonus(**entries: int) -> Mapping[GlyphFamily, int]:
    return {GlyphFamily[key.upper()]: value for key, value in entries.items()}


_RELICS: Sequence[RelicDefinition] = (
    RelicDefinition(
        id="moonlit_charm",
        name="Moonlit Charm",
        description="increases soul gain by 10%",
        modifier=RelicModifier(soul_scale=0.10),
    ),
    RelicDefinition(
        id="storm_prism",
        name="Storm Prism",
        description="amplifies weapon damage by 12%",
        modifier=RelicModifier(damage_scale=0.12),
    ),
    RelicDefinition(
        id="blood_chalice",
        name="Blood Chalice",
        description="adds 4% life steal to all attacks",
        modifier=RelicModifier(lifesteal_bonus=0.04),
    ),
    RelicDefinition(
        id="gale_idols",
        name="Gale Idols",
        description="boosts salvage earnings by 20%",
        modifier=RelicModifier(salvage_scale=0.20),
    ),
    RelicDefinition(
        id="iron_bark_totem",
        name="Iron Bark Totem",
        description="fortifies defenses by 15%",
        modifier=RelicModifier(defense_scale=0.15),
    ),
    RelicDefinition(
        id="phoenix_ember",
        name="Phoenix Ember",
        description="grants +15 max health and steady regeneration",
        modifier=RelicModifier(max_health=15, heal_on_pickup=30, regen_per_second=1.2),
    ),
    RelicDefinition(
        id="gravemind_bloom",
        name="Gravemind Bloom",
        description="infuses Verdant glyph energy and 5% hazard resistance",
        modifier=RelicModifier(hazard_resist=0.05, glyph_bonus=_glyph_bonus(verdant=1)),
    ),
    RelicDefinition(
        id="astral_needle",
        name="Astral Needle",
        description="reduces hazard damage by 8% and increases souls by 5%",
        modifier=RelicModifier(hazard_resist=0.08, soul_scale=0.05),
    ),
    RelicDefinition(
        id="chillwyrm_scale",
        name="Chillwyrm Scale",
        description="dampens hazard harm by 12% and adds 10 max health",
        modifier=RelicModifier(hazard_resist=0.12, max_health=10, heal_on_pickup=10),
    ),
    RelicDefinition(
        id="inferno_brand",
        name="Inferno Brand",
        description="supercharges damage output by 18%",
        modifier=RelicModifier(damage_scale=0.18),
    ),
    RelicDefinition(
        id="verdant_heart",
        name="Verdant Heart",
        description="adds 25 max health and potent regen",
        modifier=RelicModifier(max_health=25, heal_on_pickup=25, regen_per_second=1.5),
    ),
    RelicDefinition(
        id="clockwork_sigil",
        name="Clockwork Sigil",
        description="reinforces defenses by 10% and soul gain by 5%",
        modifier=RelicModifier(defense_scale=0.10, soul_scale=0.05),
    ),
    RelicDefinition(
        id="duskwalker_boots",
        name="Duskwalker Boots",
        description="slips past traps with 6% hazard resistance and +10% salvage",
        modifier=RelicModifier(hazard_resist=0.06, salvage_scale=0.10),
    ),
    RelicDefinition(
        id="sirens_locket",
        name="Siren's Locket",
        description="cushions hazard damage by 7% and adds 3% life steal",
        modifier=RelicModifier(hazard_resist=0.07, lifesteal_bonus=0.03),
    ),
    RelicDefinition(
        id="juggernaut_core",
        name="Juggernaut Core",
        description="adds 40 max health and bolsters defense by 20%",
        modifier=RelicModifier(max_health=40, heal_on_pickup=40, defense_scale=0.20),
    ),
    RelicDefinition(
        id="wraith_candle",
        name="Wraith Candle",
        description="lures more souls (+12%) and grants a Blood glyph",
        modifier=RelicModifier(soul_scale=0.12, glyph_bonus=_glyph_bonus(blood=1)),
    ),
    RelicDefinition(
        id="lantern_of_dawn",
        name="Lantern of Dawn",
        description="restores 5% hazard resistance and 1.2 regen per second",
        modifier=RelicModifier(hazard_resist=0.05, regen_per_second=1.2),
    ),
    RelicDefinition(
        id="gauntlet_coil",
        name="Gauntlet Coil",
        description="raises damage by 8% and defense by 6%",
        modifier=RelicModifier(damage_scale=0.08, defense_scale=0.06),
    ),
    RelicDefinition(
        id="frostglass_rosary",
        name="Frostglass Rosary",
        description="cuts hazard damage by 10% and adds 2% life steal",
        modifier=RelicModifier(hazard_resist=0.10, lifesteal_bonus=0.02),
    ),
    RelicDefinition(
        id="umbral_codex",
        name="Umbral Codex",
        description="awakens Clockwork glyph insight and 6% soul gain",
        modifier=RelicModifier(soul_scale=0.06, glyph_bonus=_glyph_bonus(clockwork=1)),
    ),
)

_NAME_LOOKUP: Dict[str, RelicDefinition] = {relic.name: relic for relic in _RELICS}
_ID_LOOKUP: Dict[str, RelicDefinition] = {relic.id: relic for relic in _RELICS}


def relic_definitions() -> Sequence[RelicDefinition]:
    """Return the ordered sequence of relic definitions."""

    return list(_RELICS)


def relic_names() -> List[str]:
    """Return the list of relic names for selection pools."""

    return [relic.name for relic in _RELICS]


def get_relic_definition(identifier: str) -> RelicDefinition:
    """Resolve a relic definition by id or name."""

    if identifier in _NAME_LOOKUP:
        return _NAME_LOOKUP[identifier]
    if identifier in _ID_LOOKUP:
        return _ID_LOOKUP[identifier]
    raise KeyError(identifier)


__all__ = [
    "RelicDefinition",
    "RelicModifier",
    "get_relic_definition",
    "relic_definitions",
    "relic_names",
]

