import random

from game import config
from game.combat import CombatSummary
from game.entities import Encounter, GlyphFamily, UpgradeCard, UpgradeType, WaveDescriptor
from game.game_state import GameEvent, GameState, default_upgrade_cards
from game.environment import EnvironmentDirector, EnvironmentTickResult, HazardEvent
from game.relics import get_relic_definition
from game.systems import EncounterDirector


def test_tick_advances_phase():
    state = GameState()
    state.tick(60)
    assert state.current_phase == 1
    state.tick(300)
    assert state.current_phase == 2
    assert any(event.message.startswith("Phase advanced") for event in state.event_log)


def test_tick_resolves_environment_hazards():
    rng = random.Random(1)
    state = GameState(environment_director=EnvironmentDirector(rng))
    starting_health = state.player.health

    salvaged = 0
    weather_seen = False
    for _ in range(8):
        result = state.tick(30.0)
        salvaged += sum(event.salvage_reward for event in result.barricades)
        salvaged += sum(event.amount for event in result.resource_drops)
        weather_seen = weather_seen or any(not event.ended for event in result.weather_events)

    assert state.player.health < starting_health
    assert state.active_hazards
    assert any("Hazard triggered" in event.message for event in state.event_log)
    assert all(event.damage > 0 for event in state.active_hazards)
    assert state.player.salvage >= salvaged
    assert weather_seen or any("Weather shift" in event.message for event in state.event_log)


def test_grant_experience_creates_events():
    state = GameState()
    events = state.grant_experience(100)
    assert events
    assert isinstance(events[0], GameEvent)


def test_apply_upgrade_logs_events():
    state = GameState()
    state.player.glyph_counts[GlyphFamily.BLOOD] = config.GLYPH_SET_SIZE - 1
    card = UpgradeCard(
        name="Blood Sigil",
        description="",
        type=UpgradeType.GLYPH,
        glyph_family=GlyphFamily.BLOOD,
    )
    state.apply_upgrade(card)
    assert any("Ultimate" in event.message for event in state.event_log)


def test_next_encounter_logs_and_awards_relic():
    state = GameState()
    state.encounter_director = EncounterDirector(random.Random(3))

    for _ in range(4):
        encounter = state.next_encounter()
        assert encounter.kind == "wave"

    miniboss_encounter = state.next_encounter()
    assert miniboss_encounter.kind == "miniboss"
    assert state.player.relics
    assert any("Relic acquired" in event.message for event in state.event_log)
    assert any("Relic power" in event.message for event in state.event_log)


def test_resolve_encounter_updates_state():
    state = GameState()
    state.player.health = 80
    encounter = state.next_encounter()
    assert encounter.kind == "wave"

    summary = state.resolve_encounter(encounter)

    assert summary.souls_gained > 0
    assert state.player.health <= state.player.max_health
    assert any("Resolved wave" in event.message for event in state.event_log)


def test_grant_experience_scales_with_multiplier():
    state = GameState()
    state.player.soul_multiplier = 1.5
    state.player.experience = 0
    state.grant_experience(20)
    assert state.player.experience >= 30


def test_resolve_encounter_applies_soul_multiplier():
    class StubResolver:
        def resolve_wave(self, player, wave):
            return CombatSummary(
                kind="wave",
                enemies_defeated=3,
                souls_gained=10,
                damage_taken=0,
                healing_received=0,
                duration=1.0,
                notes=[],
            )

        def resolve_miniboss(self, player, enemy):
            return self.resolve_wave(player, None)

        def resolve_final_boss(self, player, phases):
            return self.resolve_wave(player, None)

    state = GameState()
    state.player.soul_multiplier = 2.0
    state.combat_resolver = StubResolver()
    encounter = Encounter(kind="wave", wave=WaveDescriptor(phase=1, wave_index=0, enemies=[]))
    summary = state.resolve_encounter(encounter)
    assert summary.souls_gained == 20
    assert state.player.experience >= 20


def test_relic_regeneration_restores_health():
    class StaticEnvironment:
        def update(self, phase, delta_time):
            return EnvironmentTickResult(hazards=[], barricades=[], resource_drops=[], weather_events=[])

    state = GameState(environment_director=StaticEnvironment())
    state.player.health = 40
    definition = get_relic_definition("Verdant Heart")
    state.player.apply_relic_modifier(definition.modifier)
    state.tick(5.0)
    assert state.player.health > 40


def test_hazard_resistance_reduces_damage():
    class HazardEnvironment:
        def __init__(self):
            self.triggered = False

        def update(self, phase, delta_time):
            if not self.triggered:
                self.triggered = True
                hazard = HazardEvent(
                    biome="Test",
                    name="Shockwave",
                    description="",
                    damage=40,
                    slow=0.0,
                    duration=1.0,
                )
                return EnvironmentTickResult(hazards=[hazard], barricades=[], resource_drops=[], weather_events=[])
            return EnvironmentTickResult(hazards=[], barricades=[], resource_drops=[], weather_events=[])

    state = GameState(environment_director=HazardEnvironment())
    state.player.health = 100
    state.player.hazard_resistance = 0.5
    state.tick(1.0)
    assert state.player.health == 80


def test_final_encounter_triggers_final_boss_flow():
    rng = random.Random(5)
    state = GameState(
        encounter_director=EncounterDirector(rng),
        environment_director=EnvironmentDirector(random.Random(2)),
    )
    state.player.max_health = 420
    state.player.health = 420
    state.player.unlocked_weapons["Dusk Repeater"] = 3
    state.player.unlocked_weapons["Storm Siphon"] = 3
    state.player.glyph_counts[GlyphFamily.FROST] = 4
    state.player.glyph_counts[GlyphFamily.STORM] = 4
    state.player.glyph_counts[GlyphFamily.BLOOD] = 4
    state.player.glyph_sets_awarded[GlyphFamily.BLOOD] = 1

    encounter = state.final_encounter()
    assert encounter.kind == "final_boss"
    summary = state.resolve_encounter(encounter)

    assert summary.kind == "final_boss"
    assert any("final boss" in event.message.lower() for event in state.event_log)
    assert any("Dawn breaks" in event.message for event in state.event_log)


def test_default_upgrade_cards_cover_weapon_roster():
    cards = default_upgrade_cards()
    weapon_cards = [card for card in cards if card.type is UpgradeType.WEAPON]

    tiers_by_weapon = {}
    for card in weapon_cards:
        assert card.weapon_tier is not None
        tiers_by_weapon.setdefault(card.name, set()).add(card.weapon_tier)

    assert len(tiers_by_weapon) == 10
    assert tiers_by_weapon["Dusk Repeater"] == {2, 3, 4}

    for weapon, tiers in tiers_by_weapon.items():
        if weapon == "Dusk Repeater":
            continue
        assert tiers == {1, 2, 3, 4}
