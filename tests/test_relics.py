from game import config
from game.entities import GlyphFamily, Player
from game.relics import get_relic_definition, relic_names


def test_relic_catalog_matches_prd_scope():
    names = relic_names()
    assert len(names) == 20
    assert len(set(names)) == len(names)
    assert "Moonlit Charm" in names


def test_damage_relic_increases_player_multiplier():
    player = Player()
    definition = get_relic_definition("Storm Prism")
    player.apply_relic_modifier(definition.modifier)
    assert player.damage_multiplier > 1.0


def test_salvage_relic_scales_income():
    player = Player()
    definition = get_relic_definition("Gale Idols")
    player.apply_relic_modifier(definition.modifier)
    gained = player.add_salvage(10)
    assert gained > 10


def test_glyph_relic_can_unlock_set():
    player = Player()
    player.glyph_counts[GlyphFamily.CLOCKWORK] = config.GLYPH_SET_SIZE - 1
    definition = get_relic_definition("Umbral Codex")
    completed = player.apply_relic_modifier(definition.modifier)
    assert GlyphFamily.CLOCKWORK in completed
