import random

from game import content
from game.entities import EnemyLane


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


def test_enemy_instantiation_annotates_lane_and_behaviors():
    ash = content.instantiate_enemy("Ashen Rider", 1.0)
    bat = content.instantiate_enemy("Grave Bat", 1.0)

    assert ash.lane is EnemyLane.CEILING
    assert "clinger" in ash.behaviors
    assert bat.lane is EnemyLane.AIR
    assert "swoop" in bat.behaviors


def test_phase_four_roster_spans_all_lanes():
    enemies = [content.instantiate_enemy(name, 1.0) for name in content.enemy_archetypes_for_phase(4)]
    lanes = {enemy.lane for enemy in enemies}

    assert EnemyLane.GROUND in lanes
    assert EnemyLane.AIR in lanes
    assert EnemyLane.CEILING in lanes
