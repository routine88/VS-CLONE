from game.accessibility import AccessibilitySettings


def test_normalized_clamps_values():
    settings = AccessibilitySettings(
        auto_aim_radius=10.0,
        damage_taken_multiplier=0.01,
        game_speed_multiplier=10.0,
        projectile_speed_multiplier=0.01,
        message_log_size=200,
    ).normalized()

    assert settings.auto_aim_radius == 3.0
    assert settings.damage_taken_multiplier == 0.1
    assert settings.game_speed_multiplier == 1.5
    assert settings.projectile_speed_multiplier == 0.25
    assert settings.message_log_size == 20


def test_normalized_returns_self_when_in_bounds():
    settings = AccessibilitySettings().normalized()
    assert settings is not None
    assert settings.auto_aim_radius == 0.8
    assert settings.damage_taken_multiplier == 1.0
