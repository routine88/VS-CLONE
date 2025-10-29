import random

from game.combat import CombatResolver
from game.content import build_wave_descriptor, final_boss_phases, pick_miniboss
from game.entities import Enemy, EnemyLane, GlyphFamily, Player, WaveDescriptor


def test_combat_resolver_wave_scaling():
    player = Player()
    player.level = 5
    player.glyph_counts[GlyphFamily.STORM] = 2
    player.glyph_counts[GlyphFamily.BLOOD] = 3
    player.glyph_sets_awarded[GlyphFamily.BLOOD] = 1

    wave = build_wave_descriptor(phase=2, wave_index=1, rng=random.Random(4))
    resolver = CombatResolver()
    summary = resolver.resolve_wave(player, wave)

    assert summary.enemies_defeated == len(wave.enemies)
    assert summary.souls_gained > 0
    assert summary.damage_taken > 0
    assert "Player DPS" in summary.notes[0]


def test_combat_resolver_miniboss_healing_caps():
    player = Player()
    player.health = 40
    player.max_health = 120
    player.glyph_counts[GlyphFamily.BLOOD] = 6
    player.glyph_sets_awarded[GlyphFamily.BLOOD] = 1

    miniboss = pick_miniboss(phase=3, rng=random.Random(7))
    resolver = CombatResolver()
    summary = resolver.resolve_miniboss(player, miniboss)

    assert summary.healing_received <= player.max_health - player.health


def test_combat_resolver_final_boss_multiphase():
    player = Player()
    player.level = 20
    player.max_health = 320
    player.health = 320
    player.unlocked_weapons["Dusk Repeater"] = 3
    player.unlocked_weapons["Storm Siphon"] = 3
    player.glyph_counts[GlyphFamily.BLOOD] = 6
    player.glyph_sets_awarded[GlyphFamily.BLOOD] = 1
    player.glyph_counts[GlyphFamily.STORM] = 4
    player.glyph_counts[GlyphFamily.FROST] = 3

    resolver = CombatResolver()
    phases = final_boss_phases()
    summary = resolver.resolve_final_boss(player, phases)

    assert summary.kind == "final_boss"
    assert summary.enemies_defeated == len(phases)
    assert summary.damage_taken > 0
    assert any("Phase 1" in note for note in summary.notes)


def test_lane_and_behavior_modifiers_surface_in_summary_notes():
    player = Player()
    enemies = [
        Enemy(
            name="Air Striker",
            health=45,
            damage=6,
            speed=1.4,
            lane=EnemyLane.AIR,
            behaviors=("ranged",),
        ),
        Enemy(
            name="Ceiling Lurker",
            health=60,
            damage=8,
            speed=1.1,
            lane=EnemyLane.CEILING,
            behaviors=("clinger",),
        ),
    ]
    wave = WaveDescriptor(phase=3, wave_index=0, enemies=enemies)
    summary = CombatResolver().resolve_wave(player, wave)

    assert any("Lane modifier" in note for note in summary.notes)
    assert any("Behavior modifier" in note for note in summary.notes)
