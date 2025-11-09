import random

from game import config
from game.entities import GlyphFamily, Player, UpgradeCard, UpgradeType
from game.systems import (
    EncounterDirector,
    SpawnDirector,
    SpawnForecastEntry,
    UpgradeDeck,
    resolve_experience_gain,
)


def test_spawn_director_progression():
    director = SpawnDirector()
    first = director.next_interval(1)
    second = director.next_interval(1)
    assert second <= first
    assert director.max_density(1) > 0


def test_upgrade_deck_draw_respects_limit():
    deck = UpgradeDeck(
        UpgradeCard(name=str(i), description="", type=UpgradeType.SURVIVAL) for i in range(10)
    )
    random.seed(123)
    options = deck.draw_options()
    assert len(options) == 3


def test_experience_gain_levels_up_and_tracks_glyphs():
    player = Player()
    base_xp = config.LEVEL_CURVE.base_xp
    notifications = resolve_experience_gain(player, base_xp)
    assert any("Level up" in message for message in notifications)

    for _ in range(config.GLYPH_SET_SIZE):
        player.add_glyph(GlyphFamily.BLOOD)
    player.level += 1
    notifications = resolve_experience_gain(player, base_xp * 6)
    assert any("Ultimate" in message for message in notifications)


def test_encounter_director_cycles_waves_and_minibosses():
    rng = random.Random(7)
    director = EncounterDirector(rng)

    encounters = [director.next_encounter(1) for _ in range(5)]
    kinds = [enc.kind for enc in encounters]
    assert kinds.count("wave") == 4
    assert kinds[-1] == "miniboss"

    wave = encounters[0].wave
    assert wave is not None and len(wave.enemies) > 0


def test_spawn_director_forecast_and_difficulty_profiles():
    director = SpawnDirector()
    baseline = director.forecast(phase=1, waves=3)
    assert isinstance(baseline, tuple)
    assert all(isinstance(entry, SpawnForecastEntry) for entry in baseline)
    assert all(baseline[i].time < baseline[i + 1].time for i in range(len(baseline) - 1))

    director.apply_difficulty_profile("nightmare")
    harder = director.forecast(phase=1, waves=1)[0]
    assert harder.interval <= baseline[0].interval
    assert harder.max_density >= baseline[0].max_density

    director.apply_event_modifiers(density_multiplier=1.5)
    boosted = director.forecast(phase=1, waves=1, start_time=harder.time)[0]
    assert boosted.max_density >= harder.max_density
