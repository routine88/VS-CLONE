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


def score_run(result: RunResult) -> int:
    """Return the number of sigils earned from a completed run."""

    sigils = 5  # baseline for participating in a run
    if result.survived:
        sigils += 15
    sigils += len(result.relics_collected) * 3
    sigils += min(12, result.encounters_resolved // 3)

    if (
        result.survived
        and result.final_summary is not None
        and result.final_summary.kind == "final_boss"
    ):
        sigils += 12

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
