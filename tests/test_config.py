from game import config


def test_level_curve_progression():
    assert config.LEVEL_CURVE.xp_for_level(1) == 0
    assert config.LEVEL_CURVE.xp_for_level(2) == config.LEVEL_CURVE.base_xp
    assert config.LEVEL_CURVE.xp_for_level(3) > config.LEVEL_CURVE.xp_for_level(2)


def test_spawn_schedule_clamps():
    schedule = config.SPAWN_PHASES[1]
    assert schedule.interval_for_wave(0) == schedule.base_interval
    assert schedule.interval_for_wave(50) == schedule.base_interval / 4
