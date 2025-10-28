"""Tests covering the text-mode prototype runner."""

import pytest

from game.profile import PlayerProfile
from game.prototype import PrototypeSession, format_transcript, main


def test_prototype_session_generates_transcript() -> None:
    profile = PlayerProfile()
    session = PrototypeSession(profile)
    transcript = session.run(seed=1234, total_duration=120.0, tick_step=10.0)

    assert transcript.seed == 1234
    assert transcript.hunter_id == profile.active_hunter
    assert transcript.events, "expected event log entries"
    assert profile.meta.ledger.balance == transcript.sigils_earned

    rendered = format_transcript(transcript)
    assert "Nightfall Survivors Prototype Run" in rendered
    assert transcript.hunter_name in rendered


def test_main_invocation_prints_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--seed", "99", "--duration", "60", "--tick-step", "10"])
    assert exit_code == 0

    captured = capsys.readouterr().out
    assert "Nightfall Survivors Prototype Run" in captured


def test_profile_path_requires_key(tmp_path) -> None:
    profile_path = tmp_path / "profile.nfs"
    with pytest.raises(SystemExit):
        main(["--profile-path", str(profile_path)])
