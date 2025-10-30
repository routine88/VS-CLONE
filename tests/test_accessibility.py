from game.accessibility import AccessibilitySettings
from game.interactive import ArcadeEngine, InputFrame


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


def test_normalized_colorblind_mode():
    settings = AccessibilitySettings(colorblind_mode="Protanopia").normalized()
    assert settings.colorblind_mode == "protanopia"

    fallback = AccessibilitySettings(colorblind_mode="invalid").normalized()
    assert fallback.colorblind_mode == "none"


def test_audio_cues_emit_events():
    engine = ArcadeEngine(accessibility=AccessibilitySettings(audio_cues=True, colorblind_mode="deuteranopia"))
    engine.state.player.max_health = 100
    engine.state.player.health = 20
    engine._awaiting_upgrade = True  # type: ignore[attr-defined]

    snapshot = engine.step(0.1, InputFrame())

    assert snapshot.audio_cues is True
    assert snapshot.colorblind_mode == "deuteranopia"
    assert "accessibility.health.low" in snapshot.audio_events
    assert "accessibility.upgrade.prompt" in snapshot.audio_events
