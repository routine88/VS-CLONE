import random

from game import config
from game.entities import GlyphFamily
from game.environment import EnvironmentDirector
from game.game_state import GameState
from game.session import (
    RunSimulator,
    SIGIL_BASELINE,
    SIGIL_FINAL_BOSS_BONUS,
    SIGIL_SURVIVAL_BONUS,
)
from game.systems import EncounterDirector


def _build_powered_state(seed: int) -> GameState:
    state = GameState(
        environment_director=EnvironmentDirector(random.Random(seed)),
        encounter_director=EncounterDirector(random.Random(seed + 1)),
    )
    state.environment_director._cooldowns = {phase: 9999.0 for phase in config.HAZARD_PHASES}
    state.player.max_health = 480
    state.player.health = 480
    state.player.unlocked_weapons["Dusk Repeater"] = 3
    state.player.unlocked_weapons["Storm Siphon"] = 3
    state.player.glyph_counts[GlyphFamily.STORM] = config.GLYPH_SET_SIZE
    state.player.glyph_counts[GlyphFamily.FROST] = config.GLYPH_SET_SIZE
    state.player.glyph_counts[GlyphFamily.BLOOD] = config.GLYPH_SET_SIZE
    state.player.glyph_sets_awarded[GlyphFamily.BLOOD] = 1
    return state


def test_run_simulator_completes_full_session():
    state = _build_powered_state(3)
    simulator = RunSimulator(state=state, tick_step=4.0)
    result = simulator.run()

    assert result.final_summary is not None
    assert result.final_summary.kind == "final_boss"
    assert result.duration >= config.RUN_DURATION_SECONDS
    assert result.encounters_resolved >= 1
    assert result.events
    minimum_expected = SIGIL_BASELINE + SIGIL_SURVIVAL_BONUS + SIGIL_FINAL_BOSS_BONUS
    assert result.sigils_earned >= minimum_expected


def test_run_simulator_handles_defeat_before_dawn():
    state = GameState(
        environment_director=EnvironmentDirector(random.Random(11)),
        encounter_director=EncounterDirector(random.Random(12)),
    )
    state.player.max_health = 60
    state.player.health = 60
    state.player.unlocked_weapons = {"Dusk Repeater": 1}

    simulator = RunSimulator(state=state, total_duration=300.0, tick_step=6.0)
    result = simulator.run()

    assert not result.survived
    assert result.final_summary is None
    assert result.duration <= 300.0
    assert result.encounters_resolved >= 0
    assert result.sigils_earned >= SIGIL_BASELINE
