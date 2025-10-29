import random
from datetime import datetime, timedelta, timezone

from game import config
from game.environment import EnvironmentDirector
from game.game_state import GameState
from game.live_ops import activate_event, active_event, find_event, seasonal_schedule


def test_seasonal_schedule_sorted_and_complete():
    events = seasonal_schedule(2026)
    assert len(events) == 3
    assert events == sorted(events, key=lambda event: event.start)


def test_active_event_detection():
    year = datetime.now(timezone.utc).year
    events = seasonal_schedule(year)
    event = events[0]
    moment = event.start + timedelta(days=1)
    assert active_event(events, moment) == event


def test_find_event_by_id():
    events = seasonal_schedule(2025)
    event = events[1]
    found = find_event(event.id, events)
    assert found is event


def test_activate_event_adjusts_state_and_environment():
    state = GameState()
    rng_seed = 1337
    state.environment_director = EnvironmentDirector(random.Random(rng_seed))
    baseline_director = EnvironmentDirector(random.Random(rng_seed))
    events = seasonal_schedule(2027)
    event = events[0]

    activate_event(state, event)
    base_interval = config.SPAWN_PHASES[1].interval_for_wave(0)
    adjusted_interval = state.spawn_director.next_interval(1)
    assert adjusted_interval < base_interval
    assert state.spawn_director.max_density(1) > config.SPAWN_PHASES[1].max_density

    baseline_result = baseline_director.update(1, 240.0)
    tuned_result = state.environment_director.update(1, 240.0)
    assert baseline_result.hazards and tuned_result.hazards
    assert tuned_result.hazards[0].damage >= baseline_result.hazards[0].damage
    assert baseline_result.barricades and tuned_result.barricades
    assert (
        tuned_result.barricades[0].salvage_reward
        >= baseline_result.barricades[0].salvage_reward
    )
    assert state.event_log[-1].message.startswith("Seasonal event active:")
