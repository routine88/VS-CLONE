import pytest

from game import content
from game.accessibility import AccessibilitySettings
from game.audio import AudioEngine
from game.entities import Enemy, EnemyLane, UpgradeType
from game.accessibility import AccessibilitySettings
from game.interactive import ActiveEnemy, ArcadeEngine, InputFrame, Projectile, main
from game.localization import default_catalog, get_translator


def test_arcade_engine_spawns_entities():
    engine = ArcadeEngine(spawn_interval=0.1, target_duration=30.0)
    frame = None
    for _ in range(20):
        frame = engine.step(0.1, InputFrame())
    assert frame is not None
    assert len(frame.enemies) > 0
    assert frame.audio_events


def test_arcade_engine_level_up_triggers_upgrade_options():
    engine = ArcadeEngine(spawn_interval=5.0, target_duration=60.0)
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(5):
        engine._reward_enemy(enemy)  # type: ignore[attr-defined]
    snapshot = engine.step(0.1, InputFrame())
    assert snapshot.awaiting_upgrade
    assert len(snapshot.upgrade_options) >= 1
    assert "ui.level_up" in snapshot.audio_events


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
        engine._reward_enemy(enemy)  # type: ignore[attr-defined]
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


def test_damage_multiplier_scales_collision_damage():
    settings = AccessibilitySettings(damage_taken_multiplier=0.5)
    engine = ArcadeEngine(spawn_interval=10.0, target_duration=30.0, accessibility=settings)
    template = Enemy(name="Bruiser", health=50, damage=20, speed=1.0)
    foe = ActiveEnemy(template=template, x=1.0, y=engine._ground, speed=0.0, health=50.0)
    starting_health = engine.state.player.health
    engine._handle_collision(foe)  # type: ignore[attr-defined]
    assert engine.state.player.health == starting_health - 10


def test_auto_aim_radius_expands_hits():
    enemy_template = Enemy(name="Hover", health=20, damage=5, speed=1.0, lane=EnemyLane.AIR)
    projectile = Projectile(x=10.0, y=5.0, speed=0.0, damage=12.0)

    base_engine = ArcadeEngine(spawn_interval=10.0, target_duration=30.0)
    boosted_engine = ArcadeEngine(
        spawn_interval=10.0,
        target_duration=30.0,
        accessibility=AccessibilitySettings(auto_aim_radius=2.5),
    )

    base_enemy = ActiveEnemy(template=enemy_template, x=9.5, y=6.3, speed=0.0, health=20.0)
    boosted_enemy = ActiveEnemy(template=enemy_template, x=9.5, y=6.3, speed=0.0, health=20.0)

    base_engine._enemies = [base_enemy]
    base_engine._projectiles = [projectile]
    base_engine._update_projectiles(0.1)  # type: ignore[attr-defined]

    boosted_engine._enemies = [boosted_enemy]
    boosted_engine._projectiles = [Projectile(x=10.0, y=5.0, speed=0.0, damage=12.0)]
    boosted_engine._update_projectiles(0.1)  # type: ignore[attr-defined]

    assert base_enemy.health == 20.0
    assert boosted_enemy.health < 20.0


def test_message_log_respects_accessibility_limit():
    settings = AccessibilitySettings(message_log_size=2)
    engine = ArcadeEngine(spawn_interval=10.0, target_duration=30.0, accessibility=settings)
    engine._push_message("First")  # type: ignore[attr-defined]
    engine._push_message("Second")  # type: ignore[attr-defined]
    engine._push_message("Third")  # type: ignore[attr-defined]
    frame = engine.step(0.1, InputFrame())
    assert frame.messages == ["Second", "Third"]


def test_build_audio_frame_emits_instructions():
    engine = ArcadeEngine(spawn_interval=5.0, target_duration=60.0)
    enemy = content.instantiate_enemy("Swarm Thrall", 1.0)
    for _ in range(6):
        engine._reward_enemy(enemy)  # type: ignore[attr-defined]
    snapshot = engine.step(0.1, InputFrame())
    audio = AudioEngine()
    audio_frame = engine.build_audio_frame(audio, snapshot=snapshot)
    effect_ids = [instruction.clip.id for instruction in audio_frame.effects]
    assert "effects/ui.prompt" in effect_ids
    assert any(instr.action in {"play", "refresh"} for instr in audio_frame.music)


def test_main_demo_restrictions_trim_weapon_cards(monkeypatch):
    captured = {}

    def fake_wrapper(func, engine, fps):
        captured["engine"] = engine
        return None

    monkeypatch.setattr("game.interactive.curses.wrapper", fake_wrapper)

    main(["--demo"])

    engine = captured["engine"]
    deck = engine.state.upgrade_deck
    weapon_cards = {
        card.name
        for card in deck._pool  # type: ignore[attr-defined]
        if card.type is UpgradeType.WEAPON
    }
    assert len(weapon_cards) <= 4


def test_main_event_activation_adjusts_state(monkeypatch):
    captured = {}

    def fake_wrapper(func, engine, fps):
        captured["engine"] = engine
        return None

    monkeypatch.setattr("game.interactive.curses.wrapper", fake_wrapper)

    main(["--event-id", "harvest_moon", "--event-year", "2025"])

    engine = captured["engine"]
    spawn_director = engine.state.spawn_director
    environment = engine.state.environment_director

    assert spawn_director._density_scale == pytest.approx(1.25)  # type: ignore[attr-defined]
    assert environment._hazard_damage_scale == pytest.approx(1.1)  # type: ignore[attr-defined]
    assert environment._salvage_scale == pytest.approx(1.3)  # type: ignore[attr-defined]
