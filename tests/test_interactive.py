import pytest

from game import content
from game.entities import Enemy, EnemyLane
from game.interactive import ActiveEnemy, ArcadeEngine, InputFrame
from game.localization import default_catalog, get_translator
from game.game_state import GameState


def _award_enemy(engine: ArcadeEngine, template: Enemy, *, tag: str = "wave") -> None:
    foe = ActiveEnemy(
        template=template,
        x=engine.width - 2.0,
        y=engine._ground,  # type: ignore[attr-defined]
        speed=0.0,
        health=float(template.health),
        encounter_tag=tag,
    )
    engine._reward_enemy(foe)  # type: ignore[attr-defined]


def test_arcade_engine_spawns_entities():
    engine = ArcadeEngine(spawn_interval=0.1, target_duration=30.0)
    engine._encounter_timer = 0.0  # type: ignore[attr-defined]
    frame = None
    for _ in range(50):
        frame = engine.step(0.1, InputFrame())
        if frame.enemies:
            break
    assert frame is not None
    assert len(frame.enemies) > 0
    assert frame.audio_events


def test_arcade_engine_level_up_triggers_upgrade_options():
    engine = ArcadeEngine(spawn_interval=5.0, target_duration=60.0)
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(5):
        _award_enemy(engine, enemy)
    snapshot = engine.step(0.1, InputFrame())
    assert snapshot.awaiting_upgrade
    assert len(snapshot.upgrade_options) >= 1
    assert "ui.level_up" in snapshot.audio_events


def test_choose_upgrade_applies_and_resumes():
    engine = ArcadeEngine(spawn_interval=5.0, target_duration=60.0)
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(6):
        _award_enemy(engine, enemy)
    engine.step(0.1, InputFrame())
    card = engine.choose_upgrade(0)
    assert card.name
    frame = engine.step(0.1, InputFrame())
    assert not frame.awaiting_upgrade
    assert "ui.upgrade_selected" in frame.audio_events


def test_arcade_engine_messages_follow_translator():
    catalog = default_catalog()
    catalog.register_language(
        "test-lang",
        {"ui.upgrade_selected": "Elegido {name}."},
        inherit_from="en",
    )
    engine = ArcadeEngine(
        spawn_interval=5.0,
        target_duration=60.0,
        translator=get_translator("test-lang"),
    )
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(6):
        _award_enemy(engine, enemy)
    engine.step(0.1, InputFrame())
    engine.choose_upgrade(0)
    frame = engine.step(0.1, InputFrame())
    assert any(message.startswith("Elegido") for message in frame.messages)


def test_spawn_enemy_positions_respect_lane(monkeypatch):
    engine = ArcadeEngine(spawn_interval=10.0, target_duration=30.0)
    engine._rng.uniform = lambda lower, upper: lower  # type: ignore[assignment]

    def spawn_for(lane: EnemyLane) -> float:
        template = Enemy(name=f"{lane.value} foe", health=20, damage=5, speed=1.0, lane=lane)

        monkeypatch.setattr(content, "enemy_archetypes_for_phase", lambda phase: [template.name])

        def _instantiate(name: str, scale: float) -> Enemy:
            return Enemy(
                name=template.name,
                health=template.health,
                damage=template.damage,
                speed=template.speed,
                lane=template.lane,
                behaviors=template.behaviors,
            )

        monkeypatch.setattr(content, "instantiate_enemy", _instantiate)
        engine._enemies.clear()
        engine._spawn_enemy()
        return engine._enemies[-1].y

    ground_y = spawn_for(EnemyLane.GROUND)
    air_y = spawn_for(EnemyLane.AIR)
    ceiling_y = spawn_for(EnemyLane.CEILING)

    assert ground_y == pytest.approx(engine._ground)
    assert engine._ceiling + 2.5 <= air_y <= engine._ground - 2.0
    assert ceiling_y == pytest.approx(engine._ceiling + 0.5)
