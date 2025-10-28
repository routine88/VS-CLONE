import random

from game import config
from game.environment import (
    EnvironmentDirector,
    HazardEvent,
    WeatherEvent,
    hazards_for_phase,
)


def test_hazards_for_phase_returns_biome_entries():
    hazards = hazards_for_phase(1)
    assert hazards
    names = {hazard.name for hazard in hazards}
    assert "Creeping Fog" in names


def test_environment_director_emits_events_when_timer_elapses():
    rng = random.Random(0)
    director = EnvironmentDirector(rng=rng)

    hazards: list[HazardEvent] = []
    barricade_salvage = 0
    resource_salvage = 0
    weather_shifts: list[WeatherEvent] = []

    for _ in range(5):
        result = director.update(phase=1, delta_time=30.0)
        hazards.extend(result.hazards)
        barricade_salvage += sum(event.salvage_reward for event in result.barricades)
        resource_salvage += sum(event.amount for event in result.resource_drops)
        weather_shifts.extend(result.weather_events)

    assert hazards, "Expected at least one hazard event"
    for event in hazards:
        assert event.damage >= config.HAZARD_PHASES[1].scale_damage(1, 1)
        assert event.duration > 0
    assert barricade_salvage > 0
    assert resource_salvage > 0
    assert any(not event.ended for event in weather_shifts)
