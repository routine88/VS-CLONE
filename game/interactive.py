"""Terminal-playable prototype loop for Nightfall Survivors."""

from __future__ import annotations

import argparse
import curses
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from . import content
from .audio import AudioEngine, AudioFrame
from .accessibility import AccessibilitySettings
from .combat import glyph_damage_multiplier, weapon_tier
from .environment import (
    BarricadeEvent,
    EnvironmentTickResult,
    HazardEvent,
    ResourceDropEvent,
    WeatherEvent,
)
from .entities import Enemy, EnemyLane, UpgradeCard
from .game_state import GameState
from .graphics import Camera, GraphicsEngine, SceneNode
from .localization import Translator, get_translator
from .distribution import (
    DemoRestrictions,
    apply_demo_restrictions,
    default_demo_restrictions,
    demo_duration,
)
from .live_ops import SeasonalEvent, activate_event, find_event, seasonal_schedule
from .profile import PlayerProfile
from .storage import load_profile


@dataclass
class InputFrame:
    """Represents player input for a single simulation frame."""

    move_left: bool = False
    move_right: bool = False
    move_up: bool = False
    move_down: bool = False
    dash: bool = False
    activate_ultimate: bool = False


@dataclass
class Projectile:
    x: float
    y: float
    speed: float
    damage: float
    lifetime: float = 2.0


@dataclass
class ActiveEnemy:
    """Runtime wrapper that tracks an enemy's position and remaining HP."""

    template: Enemy
    x: float
    y: float
    speed: float
    health: float

    @property
    def alive(self) -> bool:
        return self.health > 0


@dataclass
class FrameSnapshot:
    """Data returned from the engine after advancing the simulation."""

    elapsed: float
    player_x: float
    player_y: float
    health: int
    max_health: int
    level: int
    experience: int
    next_level_xp: int
    phase: int
    score: int
    projectiles: Sequence[Projectile]
    enemies: Sequence[ActiveEnemy]
    salvage_total: int = 0
    salvage_gained: int = 0
    hazards: Sequence[HazardEvent] = field(default_factory=list)
    barricades: Sequence[BarricadeEvent] = field(default_factory=list)
    resource_drops: Sequence[ResourceDropEvent] = field(default_factory=list)
    weather_events: Sequence[WeatherEvent] = field(default_factory=list)
    messages: Sequence[str] = field(default_factory=list)
    audio_events: Sequence[str] = field(default_factory=list)
    awaiting_upgrade: bool = False
    upgrade_options: Sequence[UpgradeCard] = field(default_factory=list)
    survived: bool = False
    defeated: bool = False
    high_contrast: bool = False
    message_log_size: int = 8


class ArcadeEngine:
    """Arcade-style interpreter that exposes a playable loop."""

    def __init__(
        self,
        *,
        width: int = 80,
        height: int = 20,
        state: Optional[GameState] = None,
        profile: PlayerProfile | None = None,
        spawn_interval: float = 2.0,
        target_duration: float = 300.0,
        translator: Translator | None = None,
        accessibility: AccessibilitySettings | None = None,
    ) -> None:
        if width < 40 or height < 10:
            raise ValueError("playfield too small for interaction")

        self.width = float(width)
        self.height = float(height)
        self._ground = self.height - 2.0
        self._ceiling = 1.0
        if state is None and profile is not None:
            state = profile.start_run()
        if state is None:
            self._translator = translator or get_translator()
            self._state = GameState(translator=self._translator)
        else:
            if translator is not None:
                state.translator = translator
            self._state = state
            self._translator = translator or state.translator
        self._profile: PlayerProfile | None = profile
        self._accessibility = (accessibility or AccessibilitySettings()).normalized()
        self._player_position = [5.0, self.height / 2.0]
        self._player_velocity = [0.0, 0.0]
        self._dash_cooldown = 0.0
        self._ultimate_cooldown = 0.0
        self._weapons: dict[str, float] = {}
        self._projectiles: List[Projectile] = []
        self._enemies: List[ActiveEnemy] = []
        self._messages: List[str] = []
        self._audio_events: List[str] = []
        self._spawn_timer = spawn_interval
        self._base_spawn_interval = spawn_interval
        self._elapsed = 0.0
        self._score = 0
        self._awaiting_upgrade = False
        self._upgrade_options: List[UpgradeCard] = []
        self._target_duration = target_duration
        self._defeated = False
        self._music_started = False
        self._victory_announced = False
        self._defeat_announced = False
        self._rng = random.Random()
        self._last_snapshot: FrameSnapshot | None = None
        self._environment_time_scale = 300.0 / 75.0
        self._environment_events = EnvironmentTickResult([], [], [], [])
        self._environment_salvage_gained = 0

        self._refresh_weapon_cache()

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def defeated(self) -> bool:
        return self._defeated

    @property
    def awaiting_upgrade(self) -> bool:
        return self._awaiting_upgrade

    @property
    def upgrade_options(self) -> Sequence[UpgradeCard]:
        return tuple(self._upgrade_options)

    @property
    def translator(self) -> Translator:
        return self._translator

    @property
    def accessibility(self) -> AccessibilitySettings:
        return self._accessibility

    @property
    def profile(self) -> PlayerProfile | None:
        return self._profile

    def step(self, delta_time: float, inputs: InputFrame) -> FrameSnapshot:
        """Advance the engine and return a snapshot for presentation."""

        if delta_time <= 0:
            raise ValueError("delta_time must be positive")

        delta_time *= self._accessibility.game_speed_multiplier

        if self._defeated or self._elapsed >= self._target_duration:
            return self._snapshot()

        environment_result = self._state.tick(delta_time * self._environment_time_scale)
        self._process_environment_tick(environment_result)

        self._elapsed += delta_time

        if self._defeated or self._elapsed >= self._target_duration:
            return self._snapshot()

        self._dash_cooldown = max(0.0, self._dash_cooldown - delta_time)
        self._ultimate_cooldown = max(0.0, self._ultimate_cooldown - delta_time)

        self._apply_movement(delta_time, inputs)
        self._handle_weapons(delta_time)
        self._update_projectiles(delta_time)
        self._spawn_timer -= delta_time
        while self._spawn_timer <= 0 and not self._awaiting_upgrade:
            self._spawn_enemy()
            phase_factor = 0.9 ** max(0, self._state.current_phase - 1)
            self._spawn_timer += max(0.6, self._base_spawn_interval * phase_factor)

        self._advance_enemies(delta_time)
        if inputs.activate_ultimate:
            self._trigger_ultimate()

        return self._snapshot()

    def choose_upgrade(self, index: int) -> UpgradeCard:
        """Apply the selected upgrade and resume play."""

        if not self._awaiting_upgrade:
            raise RuntimeError("no upgrade pending")
        if index < 0 or index >= len(self._upgrade_options):
            raise IndexError("upgrade index out of range")

        card = self._upgrade_options[index]
        self._state.apply_upgrade(card)
        self._push_message(self._translate("ui.upgrade_selected", name=card.name))
        self._push_audio("ui.upgrade_selected")
        self._awaiting_upgrade = False
        self._upgrade_options = []
        self._refresh_weapon_cache()
        return card

    def _process_environment_tick(self, result: EnvironmentTickResult) -> None:
        """Translate environment outputs into arcade-facing feedback."""

        self._environment_events = EnvironmentTickResult(
            list(result.hazards),
            list(result.barricades),
            list(result.resource_drops),
            list(result.weather_events),
        )
        self._environment_salvage_gained = 0

        for hazard in result.hazards:
            self._push_message(
                self._translate(
                    "game.hazard_trigger",
                    name=hazard.name,
                    biome=hazard.biome,
                    damage=hazard.damage,
                )
            )
            if hazard.slow > 0:
                percent = int(hazard.slow * 100)
                duration = int(round(hazard.duration))
                self._push_message(
                    self._translate(
                        "game.hazard_slow",
                        name=hazard.name,
                        percent=percent,
                        duration=duration,
                    )
                )
            self._push_audio("environment.hazard")

        for barricade in result.barricades:
            self._environment_salvage_gained += barricade.salvage_reward
            self._push_message(
                self._translate(
                    "game.barricade_cleared",
                    name=barricade.name,
                    salvage=barricade.salvage_reward,
                )
            )
            self._push_audio("environment.salvage")

        for drop in result.resource_drops:
            self._environment_salvage_gained += drop.amount
            self._push_message(
                self._translate(
                    "game.salvage_collected",
                    name=drop.name,
                    amount=drop.amount,
                )
            )
            self._push_audio("environment.salvage")

        for weather in result.weather_events:
            if weather.ended:
                self._push_message(self._translate("game.weather_clear"))
                self._push_audio("environment.weather.clear")
            else:
                movement = int(weather.movement_modifier * 100)
                vision = int(weather.vision_modifier * 100)
                self._push_message(
                    self._translate(
                        "game.weather_change",
                        name=weather.name,
                        description=weather.description,
                        movement=movement,
                        vision=vision,
                    )
                )
                self._push_audio("environment.weather.change")

        if self._state.player.health <= 0 and not self._defeated:
            self._defeated = True
            self._push_message(self._translate("game.environment_defeat"))
            if not self._defeat_announced:
                self._push_audio("run.defeat")
                self._defeat_announced = True

    def _push_message(self, message: str) -> None:
        self._messages.append(message)
        limit = max(1, int(self._accessibility.message_log_size))
        if len(self._messages) > limit:
            self._messages = self._messages[-limit:]

    def _push_audio(self, event: str) -> None:
        self._audio_events.append(event)

    def _apply_movement(self, delta_time: float, inputs: InputFrame) -> None:
        speed = 14.0
        vertical_speed = 10.0
        dash_strength = 26.0

        vx = 0.0
        vy = 0.0
        if inputs.move_left:
            vx -= speed
        if inputs.move_right:
            vx += speed
        if inputs.move_up:
            vy -= vertical_speed
        if inputs.move_down:
            vy += vertical_speed

        if inputs.dash and self._dash_cooldown == 0.0:
            vx += dash_strength
            self._dash_cooldown = 2.0

        self._player_velocity[0] = vx
        self._player_velocity[1] = vy

        self._player_position[0] = max(1.0, min(self.width - 2.0, self._player_position[0] + vx * delta_time))
        self._player_position[1] = max(self._ceiling, min(self._ground, self._player_position[1] + vy * delta_time))

    def _handle_weapons(self, delta_time: float) -> None:
        multiplier = glyph_damage_multiplier(self._state.player)
        for weapon, tier in list(self._state.player.unlocked_weapons.items()):
            stats = weapon_tier(weapon, tier)
            if stats is None:
                continue

            remaining = self._weapons.setdefault(weapon, 0.0)
            remaining -= delta_time
            while remaining <= 0 and not self._awaiting_upgrade:
                remaining += stats.cooldown
                self._fire_projectiles(stats, multiplier)
            self._weapons[weapon] = remaining

    def _fire_projectiles(self, stats, multiplier: float) -> None:
        base_y = self._player_position[1]
        spread = 0.35 if stats.projectiles > 1 else 0.0
        for index in range(stats.projectiles):
            offset = (index - (stats.projectiles - 1) / 2.0) * spread
            proj = Projectile(
                x=self._player_position[0] + 1.5,
                y=max(self._ceiling, min(self._ground, base_y + offset)),
                speed=28.0 * self._accessibility.projectile_speed_multiplier,
                damage=stats.damage * multiplier,
            )
            self._projectiles.append(proj)
            self._push_audio("combat.weapon_fire")

    def _update_projectiles(self, delta_time: float) -> None:
        updated: List[Projectile] = []
        for projectile in self._projectiles:
            projectile.lifetime -= delta_time
            projectile.x += projectile.speed * delta_time
            if projectile.lifetime <= 0 or projectile.x > self.width - 1:
                continue

            hit_enemy = None
            for enemy in self._enemies:
                if not enemy.alive:
                    continue
                if (
                    abs(enemy.y - projectile.y) <= self._accessibility.auto_aim_radius
                    and projectile.x >= enemy.x
                ):
                    hit_enemy = enemy
                    break

            if hit_enemy:
                hit_enemy.health -= projectile.damage
                if hit_enemy.health <= 0:
                    self._reward_enemy(hit_enemy.template)
                continue

            updated.append(projectile)
        self._projectiles = updated

    def _reward_enemy(self, enemy: Enemy) -> None:
        self._score += enemy.health * 4
        xp = max(4, enemy.health // 2)
        self._push_audio("combat.enemy_down")
        notifications = self._state.grant_experience(xp)
        for event in notifications:
            self._push_message(event.message)
        if any(event.message.startswith("Level up!") for event in notifications):
            self._upgrade_options = list(self._state.draw_upgrades())
            self._awaiting_upgrade = True
            self._push_audio("ui.level_up")
            self._push_audio("ui.upgrade_presented")

    def _spawn_enemy(self) -> None:
        archetypes = content.enemy_archetypes_for_phase(self._state.current_phase)
        if not archetypes:
            return
        name = self._rng.choice(archetypes)
        scale = 1.0 + 0.05 * self._state.current_phase
        enemy = content.instantiate_enemy(name, scale)
        if enemy.lane is EnemyLane.GROUND:
            y = self._ground
        elif enemy.lane is EnemyLane.AIR:
            lower = self._ceiling + 2.5
            upper = self._ground - 2.0
            y = self._rng.uniform(lower, upper)
        else:
            y = self._ceiling + 0.5

        base_speed = 3.5 + enemy.speed * 1.8
        if "dash" in enemy.behaviors or "pounce" in enemy.behaviors:
            base_speed += 1.6
        if "kamikaze" in enemy.behaviors:
            base_speed += 2.4
        if "slow" in enemy.behaviors:
            base_speed -= 0.8

        active = ActiveEnemy(
            template=enemy,
            x=self.width - 2.0,
            y=y,
            speed=max(1.5, base_speed),
            health=float(enemy.health),
        )
        self._enemies.append(active)
        self._push_audio("combat.enemy_spawn")

    def _advance_enemies(self, delta_time: float) -> None:
        surviving: List[ActiveEnemy] = []
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            enemy.x -= enemy.speed * delta_time
            if enemy.template.lane is EnemyLane.GROUND:
                enemy.y = max(self._ground - 0.2, min(self._ground, enemy.y + delta_time * 6.0))
            elif enemy.template.lane is EnemyLane.AIR:
                if "swoop" in enemy.template.behaviors or "pounce" in enemy.template.behaviors:
                    target = self._player_position[1]
                    enemy.y += (target - enemy.y) * min(1.0, delta_time * 1.8)
                else:
                    wave = math.sin(self._elapsed * 2.2 + enemy.x * 0.08)
                    enemy.y += wave * delta_time * 6.0
                enemy.y = max(self._ceiling + 0.5, min(self._ground - 1.0, enemy.y))
            else:
                if "clinger" in enemy.template.behaviors and enemy.x < self.width * 0.55:
                    enemy.y = min(self._ground - 0.6, enemy.y + delta_time * 9.0)
                else:
                    enemy.y = max(self._ceiling + 0.3, enemy.y - delta_time * 6.5)
            if enemy.x <= 1.5:
                self._handle_collision(enemy)
                continue
            surviving.append(enemy)
        self._enemies = surviving

    def _handle_collision(self, enemy: ActiveEnemy) -> None:
        damage = max(1, enemy.template.damage)
        if "kamikaze" in enemy.template.behaviors:
            damage = int(damage * 1.5)
        scaled_damage = max(
            1, int(round(damage * self._accessibility.damage_taken_multiplier))
        )
        self._state.player.health = max(0, self._state.player.health - scaled_damage)
        self._push_message(
            self._translate(
                "ui.damage_taken", enemy=enemy.template.name, damage=scaled_damage
            )
        )
        self._push_audio("player.damage")
        if self._state.player.health == 0:
            self._defeated = True
            if not self._defeat_announced:
                self._push_audio("run.defeat")
                self._defeat_announced = True

    def _trigger_ultimate(self) -> None:
        if self._ultimate_cooldown > 0:
            return
        sets_ready = sum(self._state.player.glyph_sets_awarded.values())
        if sets_ready <= 0:
            return

        damage = 120 + sets_ready * 45
        hits = 0
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            enemy.health -= damage
            if enemy.health <= 0:
                hits += 1
                self._reward_enemy(enemy.template)
        if hits:
            self._push_message(self._translate("ui.ultimate_ready"))
            self._ultimate_cooldown = 18.0
            self._push_audio("combat.ultimate")

    def _snapshot(self) -> FrameSnapshot:
        player = self._state.player
        next_level = player.level + 1
        from .config import LEVEL_CURVE

        survived = self._elapsed >= self._target_duration and not self._defeated

        if not self._music_started:
            self._push_audio("music.start")
            self._music_started = True
        if survived and not self._victory_announced:
            self._push_audio("run.victory")
            self._victory_announced = True
        if self._defeated and not self._defeat_announced:
            self._push_audio("run.defeat")
            self._defeat_announced = True

        snapshot = FrameSnapshot(
            elapsed=self._elapsed,
            player_x=self._player_position[0],
            player_y=self._player_position[1],
            health=player.health,
            max_health=player.max_health,
            level=player.level,
            experience=player.experience,
            next_level_xp=LEVEL_CURVE.xp_for_level(next_level),
            phase=self._state.current_phase,
            score=self._score,
            salvage_total=player.salvage,
            salvage_gained=self._environment_salvage_gained,
            projectiles=list(self._projectiles),
            enemies=list(self._enemies),
            hazards=list(self._environment_events.hazards),
            barricades=list(self._environment_events.barricades),
            resource_drops=list(self._environment_events.resource_drops),
            weather_events=list(self._environment_events.weather_events),
            messages=list(self._messages),
            audio_events=list(self._audio_events),
            awaiting_upgrade=self._awaiting_upgrade,
            upgrade_options=list(self._upgrade_options),
            survived=survived,
            defeated=self._defeated,
            high_contrast=self._accessibility.high_contrast,
            message_log_size=self._accessibility.message_log_size,
        )
        self._last_snapshot = snapshot
        self._audio_events = []
        return snapshot

    def _refresh_weapon_cache(self) -> None:
        for weapon in self._state.player.unlocked_weapons:
            self._weapons.setdefault(weapon, 0.0)

    def _translate(self, key: str, **params) -> str:
        return self._translator.translate(key, **params)

    @property
    def last_snapshot(self) -> FrameSnapshot | None:
        """Expose the most recent frame snapshot for external systems."""

        return self._last_snapshot

    def build_scene_nodes(self, snapshot: FrameSnapshot | None = None) -> Sequence[SceneNode]:
        """Convert gameplay state into a scene graph for the graphics engine."""

        snap = snapshot or self._last_snapshot
        if snap is None:
            raise RuntimeError("no snapshot available to convert into scene nodes")

        nodes: List[SceneNode] = []
        nodes.append(
            SceneNode(
                id="player",
                position=(snap.player_x, snap.player_y),
                layer="actors",
                sprite_id="actors/player",
                metadata={"kind": "player", "health": snap.health, "max_health": snap.max_health},
            )
        )

        nodes.append(
            SceneNode(
                id="background",
                position=(snap.player_x, self.height / 2.0),
                layer="background",
                sprite_id="environment/dusk",  # allows art swaps per biome later
                parallax=0.25,
                metadata={"kind": "background", "phase": snap.phase},
            )
        )

        for index, enemy in enumerate(snap.enemies):
            if not enemy.alive:
                continue
            lane = enemy.template.lane.value
            nodes.append(
                SceneNode(
                    id=f"enemy-{index}",
                    position=(enemy.x, enemy.y),
                    layer=f"actors.enemies.{lane}",
                    sprite_id=f"enemies/{enemy.template.name}",
                    metadata={
                        "kind": "enemy",
                        "name": enemy.template.name,
                        "lane": lane,
                        "behaviors": tuple(enemy.template.behaviors),
                    },
                )
            )

        for index, projectile in enumerate(snap.projectiles):
            nodes.append(
                SceneNode(
                    id=f"projectile-{index}",
                    position=(projectile.x, projectile.y),
                    layer="projectiles",
                    sprite_id="projectiles/basic",
                    metadata={"kind": "projectile", "damage": projectile.damage},
                )
            )

        return nodes

    def render_frame(
        self,
        graphics: GraphicsEngine,
        *,
        snapshot: FrameSnapshot | None = None,
        camera: Camera | None = None,
        time_override: float | None = None,
    ) -> "RenderFrame":
        """Build a renderable frame using the provided graphics engine."""

        snap = snapshot or self._last_snapshot
        if snap is None:
            raise RuntimeError("render_frame requires a snapshot; call step() first")

        nodes = self.build_scene_nodes(snap)
        camera = camera or Camera(position=(snap.player_x, self.height / 2.0), viewport=graphics.viewport)
        timestamp = time_override if time_override is not None else snap.elapsed
        return graphics.build_frame(nodes, camera=camera, time=timestamp, messages=snap.messages)

    def build_audio_frame(
        self,
        audio: AudioEngine,
        *,
        snapshot: FrameSnapshot | None = None,
        time_override: float | None = None,
    ) -> AudioFrame:
        """Generate audio cues for the given snapshot using ``audio``."""

        snap = snapshot or self._last_snapshot
        if snap is None:
            raise RuntimeError("build_audio_frame requires a snapshot; call step() first")

        timestamp = time_override if time_override is not None else snap.elapsed
        return audio.build_frame(snap.audio_events, time=timestamp)


def _run_curses_loop(
    stdscr: "curses._CursesWindow", engine: ArcadeEngine, fps: float
) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    tick = 1.0 / fps
    last_time = time.monotonic()

    while True:
        now = time.monotonic()
        delta = now - last_time
        last_time = now

        inputs = InputFrame()
        while True:
            key = stdscr.getch()
            if key == -1:
                break
            if key in (ord("q"), ord("Q")):
                return
            if engine.defeated:
                continue
            if engine.state.player.health <= 0:
                continue
            if key == curses.KEY_LEFT:
                inputs.move_left = True
            elif key == curses.KEY_RIGHT:
                inputs.move_right = True
            elif key == curses.KEY_UP:
                inputs.move_up = True
            elif key == curses.KEY_DOWN:
                inputs.move_down = True
            elif key in (ord(" "), ord("d"), ord("D")):
                inputs.dash = True
            elif key in (ord("u"), ord("U")):
                inputs.activate_ultimate = True
            elif engine.state.player.health > 0 and engine.awaiting_upgrade and key in (ord("1"), ord("2"), ord("3")):
                choice = key - ord("1")
                if choice < len(engine.upgrade_options):
                    engine.choose_upgrade(choice)

        snapshot = engine.step(max(delta, tick), inputs)

        stdscr.erase()
        _render(stdscr, snapshot, engine.width, engine.height, engine.translator)
        stdscr.refresh()

        if snapshot.defeated or snapshot.survived:
            time.sleep(2.0)
            return

        sleep_time = tick - (time.monotonic() - now)
        if sleep_time > 0:
            time.sleep(sleep_time)


def _render(
    stdscr: "curses._CursesWindow",
    snapshot: FrameSnapshot,
    width: float,
    height: float,
    translator: Translator,
) -> None:
    status = translator.translate(
        "ui.arcade_status",
        time=snapshot.elapsed,
        phase=snapshot.phase,
        level=snapshot.level,
        xp=snapshot.experience,
        next_xp=snapshot.next_level_xp,
        hp=snapshot.health,
        max_hp=snapshot.max_health,
        score=snapshot.score,
    )
    stdscr.addstr(0, 0, status[: int(width)])

    vertical_border = "|" if not snapshot.high_contrast else "#"
    horizontal_border = "-" if not snapshot.high_contrast else "#"
    player_char = "@" if not snapshot.high_contrast else "█"
    enemy_char = "E" if not snapshot.high_contrast else "▓"
    projectile_char = "-" if not snapshot.high_contrast else "━"

    for y in range(int(height)):
        stdscr.addstr(y, 0, vertical_border)
        stdscr.addstr(y, int(width) - 1, vertical_border)
    for x in range(int(width)):
        stdscr.addstr(int(height) - 1, x, horizontal_border)

    stdscr.addstr(int(snapshot.player_y), int(snapshot.player_x), player_char)

    for enemy in snapshot.enemies:
        if not enemy.alive:
            continue
        stdscr.addstr(int(enemy.y), max(1, int(enemy.x)), enemy_char)

    for projectile in snapshot.projectiles:
        stdscr.addstr(
            int(projectile.y),
            min(int(width) - 2, int(projectile.x)),
            projectile_char,
        )

    row = 1
    visible_messages = snapshot.messages[-min(
        max(1, int(snapshot.message_log_size)), max(1, int(height) - 2)
    ) :]
    for message in visible_messages:
        stdscr.addstr(row, int(width) // 2, message[: int(width / 2) - 2])
        row += 1

    if snapshot.awaiting_upgrade:
        stdscr.addstr(2, 2, translator.translate("ui.upgrade_prompt"))
        for idx, option in enumerate(snapshot.upgrade_options, start=1):
            stdscr.addstr(
                3 + idx,
                4,
                translator.translate("ui.upgrade_option", index=idx, name=option.name),
            )

    if snapshot.defeated:
        stdscr.addstr(
            int(height) // 2,
            int(width) // 2 - 6,
            translator.translate("ui.run_failed"),
        )
    elif snapshot.survived:
        stdscr.addstr(
            int(height) // 2,
            int(width) // 2 - 6,
            translator.translate("ui.run_survived"),
        )


def launch_playable(
    duration: float = 300.0,
    fps: float = 30.0,
    *,
    language: str = "en",
    accessibility: AccessibilitySettings | None = None,
    profile: PlayerProfile | None = None,
    demo_restrictions: DemoRestrictions | None = None,
    seasonal_event: SeasonalEvent | None = None,
) -> None:
    """Entry point that spins up the curses loop."""

    translator = get_translator(language)
    active_profile = profile or PlayerProfile()

    if demo_restrictions is not None:
        apply_demo_restrictions(active_profile, demo_restrictions)

    state = active_profile.start_run()
    state.translator = translator

    if seasonal_event is not None:
        activate_event(state, seasonal_event)

    target_duration = (
        demo_duration(duration, demo_restrictions)
        if demo_restrictions is not None
        else duration
    )

    engine = ArcadeEngine(
        target_duration=target_duration,
        translator=translator,
        accessibility=accessibility,
        state=state,
        profile=active_profile,
    )
    curses.wrapper(_run_curses_loop, engine, fps)


def _profile_from_args(args: argparse.Namespace) -> PlayerProfile:
    if args.profile_path:
        if not args.key:
            raise SystemExit("--profile-path requires --key for decryption")
        return load_profile(args.profile_path, key=args.key)
    return PlayerProfile()


def main(argv: Optional[Sequence[str]] = None) -> None:
    translator = get_translator()
    parser = argparse.ArgumentParser(description=translator.translate("cli.description"))
    parser.add_argument(
        "--duration",
        type=float,
        default=300.0,
        help=translator.translate("cli.help.duration"),
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help=translator.translate("cli.help.fps"),
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help=translator.translate("cli.help.language"),
    )
    parser.add_argument(
        "--assist-radius",
        type=float,
        help=translator.translate("cli.help.assist_radius"),
    )
    parser.add_argument(
        "--damage-multiplier",
        type=float,
        help=translator.translate("cli.help.damage_multiplier"),
    )
    parser.add_argument(
        "--speed-scale",
        type=float,
        help=translator.translate("cli.help.speed_scale"),
    )
    parser.add_argument(
        "--projectile-speed",
        type=float,
        help=translator.translate("cli.help.projectile_speed"),
    )
    parser.add_argument(
        "--high-contrast",
        action="store_true",
        help=translator.translate("cli.help.high_contrast"),
    )
    parser.add_argument(
        "--message-log",
        type=int,
        help=translator.translate("cli.help.message_log"),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help=translator.translate("cli.help.demo"),
    )
    parser.add_argument(
        "--event-id",
        type=str,
        help=translator.translate("cli.help.event_id"),
    )
    parser.add_argument(
        "--event-year",
        type=int,
        help=translator.translate("cli.help.event_year"),
    )
    parser.add_argument(
        "--profile-path",
        type=str,
        help=translator.translate("cli.help.profile_path"),
    )
    parser.add_argument(
        "--key",
        type=str,
        help=translator.translate("cli.help.key"),
    )
    args = parser.parse_args(argv)

    settings_kwargs = {}
    if args.assist_radius is not None:
        settings_kwargs["auto_aim_radius"] = args.assist_radius
    if args.damage_multiplier is not None:
        settings_kwargs["damage_taken_multiplier"] = args.damage_multiplier
    if args.speed_scale is not None:
        settings_kwargs["game_speed_multiplier"] = args.speed_scale
    if args.projectile_speed is not None:
        settings_kwargs["projectile_speed_multiplier"] = args.projectile_speed
    if args.high_contrast:
        settings_kwargs["high_contrast"] = True
    if args.message_log is not None:
        settings_kwargs["message_log_size"] = args.message_log

    accessibility = (
        AccessibilitySettings(**settings_kwargs) if settings_kwargs else None
    )

    profile = _profile_from_args(args)
    restrictions = default_demo_restrictions() if args.demo else None
    seasonal = None
    if args.event_id:
        events = seasonal_schedule(args.event_year)
        seasonal = find_event(args.event_id, events)

    launch_playable(
        duration=args.duration,
        fps=args.fps,
        language=args.language,
        accessibility=accessibility,
        profile=profile,
        demo_restrictions=restrictions,
        seasonal_event=seasonal,
    )


if __name__ == "__main__":  # pragma: no cover
    main()

