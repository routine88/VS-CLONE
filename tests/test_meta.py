import pytest

from game.combat import CombatSummary
from game.meta import (
    MetaProgressionSystem,
    MetaRequirement,
    SigilLedger,
    Unlockable,
    default_unlocks,
)
from game.session import RunResult, score_run


def _run_result(
    *,
    survived: bool,
    relics: int,
    encounters: int,
    final_boss: bool,
) -> RunResult:
    summary = None
    if final_boss:
        summary = CombatSummary(
            kind="final_boss",
            enemies_defeated=1,
            damage_taken=0,
            healing_received=0,
            souls_gained=0,
            duration=12.0,
            notes=["Final foe banished."],
        )
    result = RunResult(
        survived=survived,
        duration=1200.0,
        encounters_resolved=encounters,
        relics_collected=[f"Relic {i}" for i in range(relics)],
        events=[],
        final_summary=summary,
    )
    result.sigils_earned = score_run(result)
    return result


def test_meta_progression_records_sigil_rewards():
    ledger = SigilLedger()
    system = MetaProgressionSystem(ledger=ledger)
    result = _run_result(survived=True, relics=3, encounters=12, final_boss=True)

    earned = system.record_run(result)

    assert earned == result.sigils_earned
    assert ledger.balance == earned


def test_available_unlocks_respect_requirements():
    ledger = SigilLedger()
    system = MetaProgressionSystem(ledger=ledger)
    result = _run_result(survived=True, relics=1, encounters=6, final_boss=False)

    available = system.available_unlocks(run_result=result)

    ids = {unlock.id for unlock in available}
    assert "hunter_lunara" in ids
    assert "weapon_bloodthorn" in ids
    assert "hunter_aurora" not in ids
    assert "weapon_nocturne" not in ids


def test_unlock_spends_sigils_and_records_progress():
    unlocks = [
        Unlockable(
            id="test_unlock",
            name="Test Unlock",
            category="hunter",
            cost=15,
            description="",
            requirements=(MetaRequirement("survive"),),
        )
    ]
    ledger = SigilLedger(balance=20)
    system = MetaProgressionSystem(unlocks=unlocks, ledger=ledger)
    result = _run_result(survived=True, relics=0, encounters=2, final_boss=False)

    system.available_unlocks(run_result=result)
    unlocked = system.unlock("test_unlock")

    assert unlocked.id == "test_unlock"
    assert ledger.balance == 5
    assert ledger.is_unlocked("test_unlock")


def test_unlock_requires_sufficient_sigils():
    unlocks = default_unlocks()
    ledger = SigilLedger(balance=10)
    system = MetaProgressionSystem(unlocks=unlocks, ledger=ledger)

    try:
        system.unlock("hunter_lunara")
    except ValueError:
        pass
    else:
        raise AssertionError("expected spending to fail with insufficient sigils")


def test_unlock_logging_tracks_requirements_and_progress():
    ledger = SigilLedger()
    system = MetaProgressionSystem(ledger=ledger)
    result = _run_result(survived=True, relics=3, encounters=12, final_boss=True)

    system.record_run(result)
    system.unlock("hunter_lunara")

    assert system.runs_recorded == 1
    assert system.total_playtime == pytest.approx(result.duration)

    log = system.unlock_log
    assert len(log) == 1
    entry = log[0]
    assert entry.unlock_id == "hunter_lunara"
    assert entry.run_index == 1
    assert entry.total_playtime == pytest.approx(result.duration)
    kinds = [status.requirement.kind for status in entry.requirements]
    assert kinds == ["encounters"]
    assert all(status.met for status in entry.requirements)
