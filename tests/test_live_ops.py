import random
from datetime import datetime, timedelta, timezone

from game import config
from game.environment import EnvironmentDirector
from game.game_state import GameState
from game.live_ops import (
    AnnualPlan,
    activate_event,
    active_event,
    annual_plan,
    content_update_schedule,
    find_event,
    find_milestone,
    find_update,
    roadmap_schedule,
    seasonal_schedule,
)


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


def test_content_update_schedule_quarterly():
    updates = content_update_schedule(2026)
    assert [update.id for update in updates] == [
        "q1_shadows_over_ravenspire",
        "q2_gilded_tempest",
        "q3_wild_hunt",
        "q4_dawnfall_reckoning",
    ]
    assert updates == sorted(updates, key=lambda update: update.start)
    assert updates[0].new_hunters and updates[0].new_glyph_sets


def test_find_update_by_id():
    updates = content_update_schedule(2025)
    target = updates[-1]
    found = find_update(target.id, updates)
    assert found is target


def test_roadmap_schedule_tracks_prd():
    milestones = roadmap_schedule(2024)
    assert [milestone.id for milestone in milestones] == [
        "concept_validation",
        "vertical_slice",
        "content_expansion",
        "polish_launch_prep",
        "early_access_launch",
    ]
    concept = milestones[0]
    assert concept.duration_weeks == 4.0
    launch = milestones[-1]
    # Early Access launch should land around week 40.
    assert (launch.start - concept.start).days == 7 * 40


def test_find_milestone_by_id():
    milestones = roadmap_schedule(2025)
    milestone = milestones[2]
    found = find_milestone(milestone.id, milestones)
    assert found is milestone


def test_annual_plan_orders_upcoming_items():
    year = 2025
    plan = annual_plan(year)
    assert isinstance(plan, AnnualPlan)
    assert len(plan.events) == 3
    assert len(plan.milestones) == 5
    assert len(plan.updates) == 4

    moment = datetime(year, 1, 1, tzinfo=timezone.utc)
    upcoming = plan.next_items(moment)
    assert upcoming[0].id == "concept_validation"
    assert upcoming[-1].id == "q4_dawnfall_reckoning"


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
