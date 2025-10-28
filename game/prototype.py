"""Text-mode prototype runner for the Nightfall Survivors simulation."""

from __future__ import annotations

import argparse
import random
import secrets
from dataclasses import dataclass
from typing import Optional, Sequence

from .environment import EnvironmentDirector
from .game_state import GameState
from .profile import PlayerProfile
from .session import RunResult, RunSimulator
from .systems import EncounterDirector


@dataclass
class PrototypeTranscript:
    """Structured record of a simulated prototype run."""

    seed: int
    hunter_id: str
    hunter_name: str
    survived: bool
    duration: float
    encounters_resolved: int
    relics_collected: Sequence[str]
    sigils_earned: int
    events: Sequence[str]
    run_result: RunResult


class PrototypeSession:
    """High level helper that executes a run and surfaces a transcript."""

    def __init__(self, profile: Optional[PlayerProfile] = None) -> None:
        self.profile = profile or PlayerProfile()

    def run(
        self,
        *,
        hunter_id: Optional[str] = None,
        seed: Optional[int] = None,
        total_duration: Optional[float] = None,
        tick_step: Optional[float] = None,
    ) -> PrototypeTranscript:
        """Execute a single simulated run and return a transcript."""

        if hunter_id:
            self.profile.set_active_hunter(hunter_id)

        run_seed = seed if seed is not None else secrets.randbelow(2**32)
        state = self._prepare_state(run_seed)
        simulator = RunSimulator(
            state,
            total_duration=total_duration or simulator_default_duration(),
            tick_step=tick_step or 5.0,
        )
        result = simulator.run()
        earned = self.profile.record_run(result)
        hunter = self.profile.hunters[self.profile.active_hunter]

        return PrototypeTranscript(
            seed=run_seed,
            hunter_id=hunter.id,
            hunter_name=hunter.name,
            survived=result.survived,
            duration=result.duration,
            encounters_resolved=result.encounters_resolved,
            relics_collected=list(result.relics_collected),
            sigils_earned=earned,
            events=[event.message for event in result.events],
            run_result=result,
        )

    def _prepare_state(self, seed: int) -> GameState:
        """Create a run-ready :class:`GameState` seeded for determinism."""

        orchestration_rng = random.Random(seed)
        encounter_seed = orchestration_rng.getrandbits(32)
        environment_seed = orchestration_rng.getrandbits(32)

        state = self.profile.start_run()
        state.encounter_director = EncounterDirector(random.Random(encounter_seed))
        state.environment_director = EnvironmentDirector(random.Random(environment_seed))
        state.event_log.clear()
        return state


def simulator_default_duration() -> float:
    """Expose the default session duration for convenience/testing."""

    from . import config

    return config.RUN_DURATION_SECONDS


def format_transcript(transcript: PrototypeTranscript) -> str:
    """Render a human-readable summary for the supplied transcript."""

    header = [
        "Nightfall Survivors Prototype Run",
        f"Hunter: {transcript.hunter_name} ({transcript.hunter_id})",
        f"Seed: {transcript.seed}",
        f"Outcome: {'Survived' if transcript.survived else 'Fallen'}",
        f"Duration: {transcript.duration:.1f}s",
        f"Encounters Resolved: {transcript.encounters_resolved}",
        f"Relics: {', '.join(transcript.relics_collected) if transcript.relics_collected else 'None'}",
        f"Sigils Earned: {transcript.sigils_earned}",
        "",
        "Event Log:",
    ]

    lines = list(header)
    for index, message in enumerate(transcript.events, start=1):
        lines.append(f"  [{index:03d}] {message}")

    summary = transcript.run_result.final_summary
    if summary is not None:
        lines.extend(
            [
                "",
                "Final Encounter Summary:",
                f"  Kind: {summary.kind.replace('_', ' ').title()}",
                f"  Duration: {summary.duration:.1f}s",
                f"  Damage Taken: {summary.damage_taken}",
                f"  Healing Received: {summary.healing_received}",
                f"  Souls Gained: {summary.souls_gained}",
            ]
        )
        for note in summary.notes:
            lines.append(f"    - {note}")

    return "\n".join(lines)


def _build_profile_from_args(args: argparse.Namespace) -> PlayerProfile:
    if args.profile_path:
        if not args.key:
            raise SystemExit("--profile-path requires --key for decryption")
        from .storage import load_profile

        return load_profile(args.profile_path, key=args.key)
    return PlayerProfile()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point used by ``python -m game.prototype``."""

    parser = argparse.ArgumentParser(description="Run a Nightfall Survivors prototype simulation.")
    parser.add_argument("--hunter", dest="hunter_id", help="Hunter identifier to pilot during the run.")
    parser.add_argument("--seed", type=int, help="Optional RNG seed for deterministic runs.")
    parser.add_argument(
        "--duration",
        type=float,
        help="Override the default session duration in seconds.",
    )
    parser.add_argument(
        "--tick-step",
        dest="tick_step",
        type=float,
        help="Simulation tick granularity in seconds.",
    )
    parser.add_argument(
        "--profile-path",
        type=str,
        help="Load an encrypted profile before running the simulation.",
    )
    parser.add_argument(
        "--key",
        type=str,
        help="Decryption key used when a profile path is provided.",
    )

    args = parser.parse_args(argv)
    profile = _build_profile_from_args(args)
    session = PrototypeSession(profile)
    transcript = session.run(
        hunter_id=args.hunter_id,
        seed=args.seed,
        total_duration=args.duration,
        tick_step=args.tick_step,
    )
    print(format_transcript(transcript))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    raise SystemExit(main())
