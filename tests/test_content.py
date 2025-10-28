import random

from game import content


def test_phase_four_enemy_roster_matches_prd_scope():
    archetypes = content.enemy_archetypes_for_phase(4)
    assert len(archetypes) == 12
    assert "Swarm Thrall" in archetypes
    assert "Ashen Rider" in archetypes


def test_elite_enemies_inject_into_waves():
    rng = random.Random(1337)
    wave = content.build_wave_descriptor(4, 6, rng)
    elite_names = set(content.elite_archetypes_for_phase(4))
    assert elite_names
    assert any(enemy.name in elite_names for enemy in wave.enemies)


def test_relic_catalog_expanded_to_twenty_entries():
    relics = content.relic_catalog()
    assert len(relics) == 20
    assert len(set(relics)) == len(relics)
