from game import content
from game.interactive import ArcadeEngine, InputFrame


def test_arcade_engine_spawns_entities():
    engine = ArcadeEngine(spawn_interval=0.1, target_duration=30.0)
    frame = None
    for _ in range(20):
        frame = engine.step(0.1, InputFrame())
    assert frame is not None
    assert len(frame.enemies) > 0


def test_arcade_engine_level_up_triggers_upgrade_options():
    engine = ArcadeEngine(spawn_interval=5.0, target_duration=60.0)
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(5):
        engine._reward_enemy(enemy)  # type: ignore[attr-defined]
    snapshot = engine.step(0.1, InputFrame())
    assert snapshot.awaiting_upgrade
    assert len(snapshot.upgrade_options) >= 1


def test_choose_upgrade_applies_and_resumes():
    engine = ArcadeEngine(spawn_interval=5.0, target_duration=60.0)
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(6):
        engine._reward_enemy(enemy)  # type: ignore[attr-defined]
    engine.step(0.1, InputFrame())
    card = engine.choose_upgrade(0)
    assert card.name
    frame = engine.step(0.1, InputFrame())
    assert not frame.awaiting_upgrade
