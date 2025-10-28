import random

from game import config
from game.environment import EnvironmentDirector, HazardEvent, hazards_for_phase


def test_hazards_for_phase_returns_biome_entries():
    hazards = hazards_for_phase(1)
    assert hazards
    names = {hazard.name for hazard in hazards}
    assert "Creeping Fog" in names


def test_environment_director_emits_events_when_timer_elapses():
    rng = random.Random(0)
    director = EnvironmentDirector(rng=rng)

    events: list[HazardEvent] = []
    # Step time forward until at least one hazard triggers.
    for _ in range(3):
        events.extend(director.update(phase=1, delta_time=30.0))

    assert events, "Expected at least one hazard event"
    for event in events:
        assert event.damage >= config.HAZARD_PHASES[1].scale_damage(1, 1)
        assert event.duration > 0
