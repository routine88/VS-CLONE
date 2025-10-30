"""Terminal-playable prototype loop for Nightfall Survivors."""

from __future__ import annotations

import argparse
import curses
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .audio import AudioEngine, AudioFrame
from .accessibility import AccessibilitySettings
from .combat import glyph_damage_multiplier, weapon_tier
from .entities import Encounter, Enemy, EnemyLane, UpgradeCard
from .game_state import GameState
from .graphics import Camera, GraphicsEngine, SceneNode
from .localization import Translator, get_translator


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
    encounter_tag: str = "wave"

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
    messages: Sequence[str] = field(default_factory=list)
    audio_events: Sequence[str] = field(default_factory=list)
    awaiting_upgrade: bool = False
    upgrade_options: Sequence[UpgradeCard] = field(default_factory=list)
    survived: bool = False
    defeated: bool = False
    high_contrast: bool = False
    message_log_size: int = 8
    relics: Sequence[str] = field(default_factory=list)


class ArcadeEngine:
    """Arcade-style interpreter that exposes a playable loop."""

    def __init__(
        self,
        *,
        width: int = 80,
        height: int = 20,
        state: Optional[GameState] = None,
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
        if state is None:
            self._translator = translator or get_translator()
            self._state = GameState(translator=self._translator)
        else:
            self._state = state
            self._translator = translator or state.translator
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
        self._pending_enemies: List[Tuple[Enemy, str]] = []
        self._encounter_timer = self._state.spawn_director.next_interval(
            self._state.current_phase
        )
        self._encounter_blocked = False
        self._force_spawn = False
        self._final_encounter_triggered = False
        self._final_encounter_complete = False
        self._final_boss_queue: List[Enemy] = []
        self._active_miniboss: ActiveEnemy | None = None
        self._active_boss: ActiveEnemy | None = None
        self._pending_relic_reward: str | None = None

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

    def step(self, delta_time: float, inputs: InputFrame) -> FrameSnapshot:
        """Advance the engine and return a snapshot for presentation."""

        if delta_time <= 0:
            raise ValueError("delta_time must be positive")

        delta_time *= self._accessibility.game_speed_multiplier

        if self._defeated or self._final_encounter_complete:
            return self._snapshot()

        self._elapsed += delta_time
        self._state.time_elapsed = self._elapsed
        new_phase = min(4, int(self._elapsed // 75) + 1)
        if new_phase != self._state.current_phase:
            self._state.current_phase = new_phase
            if not self._final_encounter_triggered:
                self._encounter_timer = self._state.spawn_director.next_interval(
                    new_phase
                )

        self._dash_cooldown = max(0.0, self._dash_cooldown - delta_time)
        self._ultimate_cooldown = max(0.0, self._ultimate_cooldown - delta_time)

        self._apply_movement(delta_time, inputs)
        self._handle_weapons(delta_time)
        self._update_projectiles(delta_time)
        self._spawn_timer -= delta_time
        self._maybe_trigger_final_encounter()
        self._process_encounter_timers(delta_time)
        self._spawn_pending_enemies()

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

    def _maybe_trigger_final_encounter(self) -> None:
        if self._final_encounter_triggered or self._defeated:
            return

        warning_window = min(self._target_duration * 0.25, 20.0)
        trigger_time = max(0.0, self._target_duration - warning_window)
        if self._elapsed >= trigger_time:
            self._start_final_encounter()

    def _process_encounter_timers(self, delta_time: float) -> None:
        if self._final_encounter_triggered or self._encounter_blocked:
            return

        if self._pending_enemies:
            self._encounter_timer = max(0.0, self._encounter_timer - delta_time)
            return

        self._encounter_timer -= delta_time
        if self._encounter_timer > 0:
            return

        encounter = self._state.next_encounter()
        self._handle_new_encounter(encounter)
        self._encounter_timer = self._state.spawn_director.next_interval(
            self._state.current_phase
        )

    def _spawn_pending_enemies(self) -> None:
        if self._awaiting_upgrade or not self._pending_enemies:
            return

        density_limit = self._state.spawn_director.max_density(self._state.current_phase)

        while self._pending_enemies and (self._force_spawn or self._spawn_timer <= 0):
            if not self._force_spawn and self._live_enemy_count() >= density_limit:
                break

            template, tag = self._pending_enemies.pop(0)
            active = self._activate_enemy(template, encounter_tag=tag)
            if tag == "miniboss":
                self._active_miniboss = active
            elif tag == "final_boss":
                self._active_boss = active

            phase_factor = 0.9 ** max(0, self._state.current_phase - 1)
            interval = max(0.4, self._base_spawn_interval * phase_factor)
            self._spawn_timer += interval
            self._force_spawn = False

    def _handle_new_encounter(self, encounter: Encounter) -> None:
        if encounter.kind == "wave" and encounter.wave:
            descriptor = encounter.wave
            for enemy in descriptor.enemies:
                self._pending_enemies.append((enemy, "wave"))
            number = descriptor.wave_index + 1
            count = len(descriptor.enemies)
            self._push_message(
                self._translate("game.wave_incoming", number=number, count=count)
            )
        elif encounter.kind == "miniboss" and encounter.miniboss:
            self._pending_enemies.clear()
            self._pending_enemies.append((encounter.miniboss, "miniboss"))
            self._encounter_blocked = True
            self._pending_relic_reward = encounter.relic_reward
            self._push_message(
                self._translate("game.miniboss_incoming", name=encounter.miniboss.name)
            )
            self._push_audio("run.miniboss_warning")
            self._force_spawn = True
            self._spawn_timer = 0.0

    def _start_final_encounter(self) -> None:
        if self._final_encounter_triggered:
            return

        encounter = self._state.final_encounter()
        self._final_encounter_triggered = True
        self._encounter_blocked = True
        self._pending_enemies.clear()
        self._final_boss_queue = []
        self._force_spawn = True
        self._spawn_timer = 0.0
        self._encounter_timer = float("inf")

        if encounter.boss_phases:
            phases = list(encounter.boss_phases)
            first = phases[0]
            self._pending_enemies.append((first, "final_boss"))
            self._final_boss_queue = phases[1:]
            base_name = first.name.split(" (")[0]
            self._push_message(self._translate("game.final_boss", name=base_name))
        else:
            self._push_message(self._translate("game.final_boss_generic"))
            self._final_encounter_complete = True
            self._encounter_blocked = True

        self._push_audio("run.final_boss_warning")
        self._push_audio("music.boss")

    def _activate_enemy(self, template: Enemy, *, encounter_tag: str) -> ActiveEnemy:
        if template.lane is EnemyLane.GROUND:
            y = self._ground
        elif template.lane is EnemyLane.AIR:
            lower = self._ceiling + 2.5
            upper = self._ground - 2.0
            y = self._rng.uniform(lower, upper)
        else:
            y = self._ceiling + 0.5

        base_speed = 3.5 + template.speed * 1.8
        if "dash" in template.behaviors or "pounce" in template.behaviors:
            base_speed += 1.6
        if "kamikaze" in template.behaviors:
            base_speed += 2.4
        if "slow" in template.behaviors:
            base_speed -= 0.8

        active = ActiveEnemy(
            template=template,
            x=self.width - 2.0,
            y=y,
            speed=max(1.5, base_speed),
            health=float(template.health),
            encounter_tag=encounter_tag,
        )
        self._enemies.append(active)
        self._push_audio("combat.enemy_spawn")
        return active

    def _live_enemy_count(self) -> int:
        return sum(1 for enemy in self._enemies if enemy.alive)

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
                    self._reward_enemy(hit_enemy)
                continue

            updated.append(projectile)
        self._projectiles = updated

    def _reward_enemy(self, enemy: ActiveEnemy) -> None:
        template = enemy.template
        self._score += template.health * 4
        xp = max(4, template.health // 2)
        self._push_audio("combat.enemy_down")
        notifications = self._state.grant_experience(xp)
        for event in notifications:
            self._push_message(event.message)
        if any(event.message.startswith("Level up!") for event in notifications):
            self._upgrade_options = list(self._state.draw_upgrades())
            self._awaiting_upgrade = True
            self._push_audio("ui.level_up")
            self._push_audio("ui.upgrade_presented")
        self._on_special_enemy_defeated(enemy)

    def _on_special_enemy_defeated(self, enemy: ActiveEnemy) -> None:
        if enemy.encounter_tag == "miniboss":
            self._active_miniboss = None
            self._encounter_blocked = False
            reward = self._pending_relic_reward
            if reward is None and self._state.player.relics:
                reward = self._state.player.relics[-1]
            if reward:
                self._push_message(self._translate("game.relic_acquired", name=reward))
                self._push_audio("run.relic_acquired")
            self._pending_relic_reward = None
        elif enemy.encounter_tag == "final_boss" and not self._final_encounter_complete:
            self._active_boss = None
            if self._final_boss_queue:
                next_phase = self._final_boss_queue.pop(0)
                self._pending_enemies.insert(0, (next_phase, "final_boss"))
                self._force_spawn = True
                self._spawn_timer = 0.0
            else:
                self._final_encounter_complete = True
                self._encounter_blocked = True
                self._push_message(self._translate("game.player_survived"))
                self._push_audio("run.final_boss_defeated")

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
                self._reward_enemy(enemy)
        if hits:
            self._push_message(self._translate("ui.ultimate_ready"))
            self._ultimate_cooldown = 18.0
            self._push_audio("combat.ultimate")

    def _snapshot(self) -> FrameSnapshot:
        player = self._state.player
        next_level = player.level + 1
        from .config import LEVEL_CURVE

        survived = self._final_encounter_complete and not self._defeated

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
            projectiles=list(self._projectiles),
            enemies=list(self._enemies),
            messages=list(self._messages),
            audio_events=list(self._audio_events),
            awaiting_upgrade=self._awaiting_upgrade,
            upgrade_options=list(self._upgrade_options),
            survived=survived,
            defeated=self._defeated,
            high_contrast=self._accessibility.high_contrast,
            message_log_size=self._accessibility.message_log_size,
            relics=list(self._state.player.relics),
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
) -> None:
    """Entry point that spins up the curses loop."""

    translator = get_translator(language)
    engine = ArcadeEngine(
        target_duration=duration,
        translator=translator,
        accessibility=accessibility,
    )
    curses.wrapper(_run_curses_loop, engine, fps)


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

    launch_playable(
        duration=args.duration,
        fps=args.fps,
        language=args.language,
        accessibility=accessibility,
    )


if __name__ == "__main__":  # pragma: no cover
    main()

