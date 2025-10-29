"""Challenge builder tests."""

import pytest

from game.challenges import (
    ChallengeConfig,
    build_config,
    decode_challenge,
    describe_challenge,
    encode_challenge,
    main,
)


def test_round_trip_encoding() -> None:
    config = build_config(
        seed=777,
        duration=600,
        difficulty="torment",
        modifiers=["fog", "double_elites"],
        banned_weapons=["weapon_crossbow"],
        required_glyphs=["glyph_blood"],
        starting_relics=["relic_moonlit_charm"],
    )

    code = encode_challenge(config)
    decoded = decode_challenge(code)

    assert decoded == config


def test_checksum_mismatch_raises_value_error() -> None:
    config = ChallengeConfig(seed=10)
    code = encode_challenge(config)
    tampered = code[:-1] + ("0" if code[-1] != "0" else "1")

    with pytest.raises(ValueError):
        decode_challenge(tampered)


def test_describe_outputs_expected_lines() -> None:
    config = build_config(seed=42, modifiers=["hardcore"])
    description = describe_challenge(config)

    assert "Seed: 42" in description
    assert "Modifiers: hardcore" in description


def test_cli_builds_challenge(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--seed",
            "55",
            "--modifier",
            "no_relics",
            "--ban",
            "weapon_nocturne_harp",
        ]
    )
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Nightfall Survivors Challenge" in output
    assert "Code: NSC1-" in output
    assert "Banned weapons: weapon_nocturne_harp" in output


def test_cli_decodes_existing_code(capsys: pytest.CaptureFixture[str]) -> None:
    code = encode_challenge(build_config(seed=100, difficulty="nightmare"))
    exit_code = main(["--decode", code])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Difficulty: nightmare" in output
