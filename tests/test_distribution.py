import pytest

from game.distribution import (
    DemoRestrictions,
    Platform,
    apply_demo_restrictions,
    configure_simulator_for_demo,
    default_build_matrix,
    default_demo_restrictions,
    demo_duration,
    validate_build_targets,
)
from game.profile import PlayerProfile
from game.session import RunSimulator


def test_default_build_matrix_has_unique_targets():
    matrix = default_build_matrix()
    assert set(matrix.keys()) == {Platform.WINDOWS, Platform.MACOS, Platform.LINUX}
    validate_build_targets(matrix.values())


def test_validate_build_targets_rejects_duplicates():
    matrix = list(default_build_matrix().values())
    duplicate = matrix[0]
    with pytest.raises(ValueError):
        validate_build_targets(matrix + [duplicate])


def test_apply_demo_restrictions_limits_profile_content():
    profile = PlayerProfile()
    restrictions = DemoRestrictions(
        max_duration=420.0,
        allowed_hunters=("hunter_varik",),
        weapon_limit=2,
        glyph_limit=2,
    )
    apply_demo_restrictions(profile, restrictions)
    assert profile.owned_hunters == {"hunter_varik"}
    assert profile.active_hunter == "hunter_varik"
    assert len(profile.available_weapon_cards) == 2
    assert len(profile.available_glyph_families) == 2


def test_configure_simulator_for_demo_caps_runtime():
    simulator = RunSimulator(total_duration=1200.0, tick_step=10.0)
    restrictions = DemoRestrictions(max_duration=300.0)
    configure_simulator_for_demo(simulator, restrictions)
    assert simulator.total_duration == pytest.approx(300.0)
    assert simulator.tick_step == pytest.approx(2.5)


def test_demo_duration_helper_uses_restrictions():
    restrictions = DemoRestrictions(max_duration=480.0)
    assert demo_duration(restrictions=restrictions) == pytest.approx(480.0)
    assert demo_duration(default_demo_restrictions().max_duration * 2) == pytest.approx(600.0)
