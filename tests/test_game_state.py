import random

from game import config
from game.entities import GlyphFamily, UpgradeCard, UpgradeType
from game.game_state import GameEvent, GameState
from game.environment import EnvironmentDirector
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

    events = []
    for _ in range(3):
        events.extend(state.tick(30.0))

    assert state.player.health < starting_health
    assert state.active_hazards
    assert any("Hazard triggered" in event.message for event in state.event_log)
    assert all(event.damage > 0 for event in state.active_hazards)


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
