"""Terminal-playable prototype loop for Nightfall Survivors."""

from __future__ import annotations

import argparse
import curses
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from . import content
from .combat import glyph_damage_multiplier, weapon_tier
from .entities import Enemy, UpgradeCard
from .game_state import GameState
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
    awaiting_upgrade: bool = False
    upgrade_options: Sequence[UpgradeCard] = field(default_factory=list)
    survived: bool = False
    defeated: bool = False


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
        self._player_position = [5.0, self.height / 2.0]
        self._player_velocity = [0.0, 0.0]
        self._dash_cooldown = 0.0
        self._ultimate_cooldown = 0.0
        self._weapons: dict[str, float] = {}
        self._projectiles: List[Projectile] = []
        self._enemies: List[ActiveEnemy] = []
        self._messages: List[str] = []
        self._spawn_timer = spawn_interval
        self._base_spawn_interval = spawn_interval
        self._elapsed = 0.0
        self._score = 0
        self._awaiting_upgrade = False
        self._upgrade_options: List[UpgradeCard] = []
        self._target_duration = target_duration
        self._defeated = False
        self._rng = random.Random()

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

    def step(self, delta_time: float, inputs: InputFrame) -> FrameSnapshot:
        """Advance the engine and return a snapshot for presentation."""

        if delta_time <= 0:
            raise ValueError("delta_time must be positive")

        if self._defeated or self._elapsed >= self._target_duration:
            return self._snapshot()

        self._elapsed += delta_time
        self._state.current_phase = min(4, int(self._elapsed // 75) + 1)

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
        self._messages.append(self._translate("ui.upgrade_selected", name=card.name))
        self._awaiting_upgrade = False
        self._upgrade_options = []
        self._refresh_weapon_cache()
        return card

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
                speed=28.0,
                damage=stats.damage * multiplier,
            )
            self._projectiles.append(proj)

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
                if abs(enemy.y - projectile.y) <= 0.8 and projectile.x >= enemy.x:
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
        notifications = self._state.grant_experience(xp)
        for event in notifications:
            self._messages.append(event.message)
        if any(event.message.startswith("Level up!") for event in notifications):
            self._upgrade_options = list(self._state.draw_upgrades())
            self._awaiting_upgrade = True

    def _spawn_enemy(self) -> None:
        archetypes = content.enemy_archetypes_for_phase(self._state.current_phase)
        if not archetypes:
            return
        name = self._rng.choice(archetypes)
        scale = 1.0 + 0.05 * self._state.current_phase
        enemy = content.instantiate_enemy(name, scale)
        active = ActiveEnemy(
            template=enemy,
            x=self.width - 2.0,
            y=max(
                self._ceiling,
                min(self._ground, 1.5 + self._rng.random() * (self._ground - 2.0)),
            ),
            speed=5.0 + 0.5 * self._state.current_phase,
            health=float(enemy.health),
        )
        self._enemies.append(active)

    def _advance_enemies(self, delta_time: float) -> None:
        surviving: List[ActiveEnemy] = []
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            enemy.x -= enemy.speed * delta_time
            if enemy.x <= 1.5:
                self._handle_collision(enemy)
                continue
            surviving.append(enemy)
        self._enemies = surviving

    def _handle_collision(self, enemy: ActiveEnemy) -> None:
        damage = max(1, enemy.template.damage)
        self._state.player.health = max(0, self._state.player.health - damage)
        self._messages.append(
            self._translate("ui.damage_taken", enemy=enemy.template.name, damage=damage)
        )
        if self._state.player.health == 0:
            self._defeated = True

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
            self._messages.append(self._translate("ui.ultimate_ready"))
            self._ultimate_cooldown = 18.0

    def _snapshot(self) -> FrameSnapshot:
        player = self._state.player
        next_level = player.level + 1
        from .config import LEVEL_CURVE

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
            awaiting_upgrade=self._awaiting_upgrade,
            upgrade_options=list(self._upgrade_options),
            survived=self._elapsed >= self._target_duration and not self._defeated,
            defeated=self._defeated,
        )
        self._messages.clear()
        return snapshot

    def _refresh_weapon_cache(self) -> None:
        for weapon in self._state.player.unlocked_weapons:
            self._weapons.setdefault(weapon, 0.0)

    def _translate(self, key: str, **params) -> str:
        return self._translator.translate(key, **params)


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

    for y in range(int(height)):
        stdscr.addstr(y, 0, "|")
        stdscr.addstr(y, int(width) - 1, "|")
    for x in range(int(width)):
        stdscr.addstr(int(height) - 1, x, "-")

    stdscr.addstr(int(snapshot.player_y), int(snapshot.player_x), "@")

    for enemy in snapshot.enemies:
        if not enemy.alive:
            continue
        stdscr.addstr(int(enemy.y), max(1, int(enemy.x)), "E")

    for projectile in snapshot.projectiles:
        stdscr.addstr(int(projectile.y), min(int(width) - 2, int(projectile.x)), "-")

    row = 1
    for message in snapshot.messages[-(int(height) - 2) :]:
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
    duration: float = 300.0, fps: float = 30.0, *, language: str = "en"
) -> None:
    """Entry point that spins up the curses loop."""

    translator = get_translator(language)
    engine = ArcadeEngine(target_duration=duration, translator=translator)
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
    args = parser.parse_args(argv)

    launch_playable(duration=args.duration, fps=args.fps, language=args.language)


if __name__ == "__main__":  # pragma: no cover
    main()

