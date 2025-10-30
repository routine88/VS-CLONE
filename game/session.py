"""Session-level simulation helpers for Nightfall Survivors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from . import config
from .combat import CombatSummary
from .game_state import GameEvent, GameState


@dataclass
class RunResult:
    """Aggregate outcome of a simulated survival run."""

    survived: bool
    duration: float
    encounters_resolved: int
    relics_collected: List[str]
    events: List[GameEvent]
    final_summary: Optional[CombatSummary] = None
    sigils_earned: int = 0


SIGIL_BASELINE = 10
SIGIL_SURVIVAL_BONUS = 30
SIGIL_FINAL_BOSS_BONUS = 25
SIGIL_PER_RELIC = 6
SIGIL_PER_ENCOUNTER = 2
SIGIL_MAX_ENCOUNTER_REWARD = 40
SIGIL_MINUTE_BUCKET = 60
SIGIL_PER_MINUTE_BUCKET = 3
SIGIL_MINUTE_BUCKET_CAP = 15
SIGIL_ENCOUNTER_MILESTONE = 5
SIGIL_ENCOUNTER_MILESTONE_BONUS = 5
SIGIL_ENCOUNTER_MILESTONE_CAP = 6


def score_run(result: RunResult) -> int:
    """Return the number of sigils earned from a completed run."""

    sigils = SIGIL_BASELINE

    if result.survived:
        sigils += SIGIL_SURVIVAL_BONUS

    sigils += len(result.relics_collected) * SIGIL_PER_RELIC
    encounter_count = result.encounters_resolved
    if SIGIL_MAX_ENCOUNTER_REWARD:
        encounter_count = min(encounter_count, SIGIL_MAX_ENCOUNTER_REWARD)
    sigils += encounter_count * SIGIL_PER_ENCOUNTER

    minute_buckets = int(result.duration // SIGIL_MINUTE_BUCKET)
    if SIGIL_MINUTE_BUCKET_CAP:
        minute_buckets = min(minute_buckets, SIGIL_MINUTE_BUCKET_CAP)
    sigils += minute_buckets * SIGIL_PER_MINUTE_BUCKET

    if SIGIL_ENCOUNTER_MILESTONE:
        milestone_count = result.encounters_resolved // SIGIL_ENCOUNTER_MILESTONE
        if SIGIL_ENCOUNTER_MILESTONE_CAP:
            milestone_count = min(milestone_count, SIGIL_ENCOUNTER_MILESTONE_CAP)
        sigils += milestone_count * SIGIL_ENCOUNTER_MILESTONE_BONUS

    if (
        result.survived
        and result.final_summary is not None
        and result.final_summary.kind == "final_boss"
    ):
        sigils += SIGIL_FINAL_BOSS_BONUS

    return sigils


class RunSimulator:
    """Drive the `GameState` through an end-to-end 20 minute session."""

    def __init__(
        self,
        state: Optional[GameState] = None,
        *,
        total_duration: float = config.RUN_DURATION_SECONDS,
        tick_step: float = 5.0,
    ) -> None:
        if total_duration <= 0:
            raise ValueError("total_duration must be positive")
        if tick_step <= 0:
            raise ValueError("tick_step must be positive")

        self.state = state or GameState()
        self.total_duration = total_duration
        self.tick_step = tick_step

    def run(self) -> RunResult:
        state = self.state
        encounters_resolved = 0

        time_until_next = state.spawn_director.next_interval(state.current_phase)
        active_phase = state.current_phase

        while state.player.health > 0 and state.time_elapsed < self.total_duration:
            remaining = self.total_duration - state.time_elapsed
            if remaining <= 0:
                break

            if time_until_next <= 1e-6:
                encounter = state.next_encounter()
                state.resolve_encounter(encounter)
                encounters_resolved += 1
                if state.player.health <= 0:
                    break
                time_until_next = state.spawn_director.next_interval(state.current_phase)
                active_phase = state.current_phase
                continue

            step = min(self.tick_step, time_until_next, remaining)
            if step <= 1e-6:
                step = min(self.tick_step, remaining)

            state.tick(step)
            time_until_next = max(0.0, time_until_next - step)

            if state.player.health <= 0:
                break

            if state.current_phase != active_phase:
                active_phase = state.current_phase
                time_until_next = state.spawn_director.next_interval(active_phase)

        final_summary: Optional[CombatSummary] = None
        survived = state.player.health > 0
        if survived:
            final_encounter = state.final_encounter()
            final_summary = state.resolve_encounter(final_encounter)
            encounters_resolved += 1
            survived = state.player.health > 0

        result = RunResult(
            survived=survived,
            duration=state.time_elapsed,
            encounters_resolved=encounters_resolved,
            relics_collected=list(state.player.relics),
            events=list(state.event_log),
            final_summary=final_summary,
        )
        result.sigils_earned = score_run(result)
        return result
