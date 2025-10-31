"""Lightweight MVP simulation focused on the core Nightfall Survivors loop."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class EnemyArchetype:
    """Definition for a simplified MVP enemy type."""

    name: str
    health: float
    speed: float
    damage: int
    xp_reward: int


@dataclass
class EnemyState:
    """Mutable runtime representation of a spawned enemy."""

    archetype: EnemyArchetype
    position: float
    health: float
    instance_id: int

    @property
    def name(self) -> str:
        return self.archetype.name

    @property
    def alive(self) -> bool:
        return self.health > 0


@dataclass
class PlayerState:
    """State container for the simulated hunter."""

    max_health: int
    speed: float
    dash_distance: float
    dash_cooldown: float
    dash_trigger: float
    base_damage: float
    base_fire_rate: float
    damage_bonus: float = 0.0
    fire_rate_bonus: float = 0.0
    health: float = field(init=False)
    position: float = 0.0
    level: int = 1
    experience: float = 0.0
    dash_timer: float = 0.0
    fire_timer: float = 0.0
    dash_count: int = 0
    upgrade_history: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.health = float(self.max_health)

    @property
    def damage_per_shot(self) -> float:
        return self.base_damage * (1.0 + self.damage_bonus)

    @property
    def fire_rate(self) -> float:
        return self.base_fire_rate * (1.0 + self.fire_rate_bonus)

    def ready_to_dash(self) -> bool:
        return self.dash_timer <= 0.0

    def reset_dash_cooldown(self) -> None:
        self.dash_timer = self.dash_cooldown

    def record_dash(self) -> None:
        self.dash_count += 1


@dataclass(frozen=True)
class MvpEnemySnapshot:
    """Serializable view of an enemy for rendering or analytics."""

    id: int
    name: str
    position: float
    health: float
    max_health: float
    damage: int
    speed: float
    xp_reward: int


@dataclass(frozen=True)
class MvpFrameSnapshot:
    """Immutable snapshot emitted after each MVP simulation tick."""

    time: float
    player_position: float
    player_health: float
    player_max_health: float
    player_level: int
    player_experience: float
    next_level_experience: float
    dash_cooldown: float
    fire_cooldown: float
    dash_ready: bool
    soul_shards: int
    enemies: Sequence[MvpEnemySnapshot]
    enemies_defeated: int
    events: Sequence[str]


@dataclass(frozen=True)
class MvpConfig:
    """Tunable parameters that drive the MVP simulation."""

    duration: float = 300.0
    tick_rate: float = 0.5
    lane_half_length: float = 12.0
    spawn_interval_start: float = 4.5
    spawn_interval_end: float = 1.5
    spawn_ramp_duration: float = 240.0
    bruiser_spawn_threshold: float = 90.0
    bruiser_spawn_growth: float = 0.45
    player_max_health: int = 120
    player_speed: float = 4.0
    player_dash_distance: float = 3.0
    player_dash_cooldown: float = 6.0
    player_dash_trigger: float = 1.1
    player_damage: float = 14.0
    player_fire_rate: float = 1.8
    experience_curve: Sequence[int] = (0, 45, 110, 190, 285)
    damage_upgrade_bonus: float = 0.35
    fire_rate_bonus: float = 0.4
    swarm_archetype: EnemyArchetype = EnemyArchetype(
        name="Grave Wisp",
        health=18.0,
        speed=1.4,
        damage=6,
        xp_reward=6,
    )
    bruiser_archetype: EnemyArchetype = EnemyArchetype(
        name="Crypt Hulk",
        health=55.0,
        speed=0.9,
        damage=14,
        xp_reward=18,
    )


@dataclass
class MvpReport:
    """Aggregated outcome of a single MVP simulation run."""

    seed: int
    survived: bool
    duration: float
    enemies_defeated: int
    enemy_type_counts: Dict[str, int]
    level_reached: int
    soul_shards: int
    upgrades_applied: List[str]
    dash_count: int
    events: List[str]
    final_health: float


class MvpSimulation:
    """Coordinator responsible for stepping through the MVP run."""

    def __init__(self, config: MvpConfig, rng: random.Random, seed_value: int) -> None:
        self.config = config
        self.rng = rng
        self.seed_value = seed_value
        self.player = PlayerState(
            max_health=config.player_max_health,
            speed=config.player_speed,
            dash_distance=config.player_dash_distance,
            dash_cooldown=config.player_dash_cooldown,
            dash_trigger=config.player_dash_trigger,
            base_damage=config.player_damage,
            base_fire_rate=config.player_fire_rate,
        )
        self.enemies: List[EnemyState] = []
        self.events: List[str] = []
        self.enemy_type_counts: Dict[str, int] = {"swarm": 0, "bruiser": 0}
        self.soul_shards = 0
        self.elapsed = 0.0
        self.next_spawn = 0.0
        self.move_direction = 1.0
        self.enemies_defeated = 0
        self._enemy_sequence = 0

    def run(self) -> MvpReport:
        config = self.config
        tick = config.tick_rate
        while self.elapsed < config.duration and self.player.health > 0:
            self.step(tick)

        return self.build_report()

    def step(self, tick: float) -> MvpFrameSnapshot:
        """Advance the simulation by ``tick`` seconds and capture a snapshot."""

        events_start = len(self.events)
        self._maybe_spawn_enemy()
        self._update_player(tick)
        self._update_enemies(tick)
        self._handle_combat(tick)
        self._handle_level_up()

        self.elapsed += tick
        self.player.dash_timer = max(0.0, self.player.dash_timer - tick)
        self.player.fire_timer = max(0.0, self.player.fire_timer - tick)

        new_events = self.events[events_start:]
        return self._snapshot(new_events)

    def _snapshot(self, new_events: Sequence[str]) -> MvpFrameSnapshot:
        curve = self.config.experience_curve
        next_level_index = min(len(curve) - 1, self.player.level)
        return MvpFrameSnapshot(
            time=min(self.elapsed, self.config.duration),
            player_position=self.player.position,
            player_health=self.player.health,
            player_max_health=float(self.player.max_health),
            player_level=self.player.level,
            player_experience=self.player.experience,
            next_level_experience=float(curve[next_level_index]),
            dash_cooldown=self.player.dash_timer,
            fire_cooldown=self.player.fire_timer,
            dash_ready=self.player.ready_to_dash(),
            soul_shards=self.soul_shards,
            enemies=tuple(
                MvpEnemySnapshot(
                    id=enemy.instance_id,
                    name=enemy.name,
                    position=enemy.position,
                    health=enemy.health,
                    max_health=enemy.archetype.health,
                    damage=enemy.archetype.damage,
                    speed=enemy.archetype.speed,
                    xp_reward=enemy.archetype.xp_reward,
                )
                for enemy in self.enemies
            ),
            enemies_defeated=self.enemies_defeated,
            events=tuple(new_events),
        )

    def build_report(self) -> MvpReport:
        config = self.config
        survived = self.player.health > 0
        return MvpReport(
            seed=self.seed_value,
            survived=survived,
            duration=min(self.elapsed, config.duration),
            enemies_defeated=self.enemies_defeated,
            enemy_type_counts=dict(self.enemy_type_counts),
            level_reached=self.player.level,
            soul_shards=self.soul_shards,
            upgrades_applied=list(self.player.upgrade_history),
            dash_count=self.player.dash_count,
            events=list(self.events),
            final_health=max(0.0, self.player.health),
        )

    def _maybe_spawn_enemy(self) -> None:
        config = self.config
        while self.elapsed >= self.next_spawn:
            progress = min(1.0, self.elapsed / max(config.spawn_ramp_duration, 1.0))
            interval = config.spawn_interval_start - (
                config.spawn_interval_start - config.spawn_interval_end
            ) * progress
            interval = max(config.spawn_interval_end, interval)
            self.next_spawn = self.elapsed + interval

            if self.elapsed < config.bruiser_spawn_threshold:
                archetype = config.swarm_archetype
                tag = "swarm"
            else:
                ramp = min(1.0, (self.elapsed - config.bruiser_spawn_threshold) / 120.0)
                bruiser_chance = min(0.9, config.bruiser_spawn_growth * ramp + 0.25)
                if self.rng.random() < bruiser_chance:
                    archetype = config.bruiser_archetype
                    tag = "bruiser"
                else:
                    archetype = config.swarm_archetype
                    tag = "swarm"

            spawn_side = self.rng.choice([-1.0, 1.0])
            position = spawn_side * config.lane_half_length
            enemy = EnemyState(
                archetype=archetype,
                position=position,
                health=archetype.health,
                instance_id=self._enemy_sequence,
            )
            self._enemy_sequence += 1
            self.enemies.append(enemy)
            self.enemy_type_counts[tag] += 1
            self.events.append(f"Spawned {archetype.name}")

    def _update_player(self, tick: float) -> None:
        if not self.enemies:
            self.player.position += self.move_direction * self.player.speed * tick * 0.25
            return

        nearest = min(self.enemies, key=lambda e: abs(e.position - self.player.position))
        distance = abs(nearest.position - self.player.position)

        if distance <= self.player.dash_trigger and self.player.ready_to_dash():
            escape_direction = -1.0 if nearest.position >= self.player.position else 1.0
            new_position = self.player.position + escape_direction * self.player.dash_distance
            self.player.position = max(
                -self.config.lane_half_length, min(self.config.lane_half_length, new_position)
            )
            self.player.reset_dash_cooldown()
            self.player.record_dash()
            self.events.append("Player dashed to safety")
            return

        if distance > self.player.dash_trigger * 4:
            self.player.position += self.move_direction * self.player.speed * tick * 0.1
            return

        if nearest.position >= self.player.position:
            self.move_direction = -1.0
        else:
            self.move_direction = 1.0
        self.player.position += self.move_direction * self.player.speed * tick * 0.6

        if abs(self.player.position) >= self.config.lane_half_length:
            self.player.position = max(
                -self.config.lane_half_length, min(self.config.lane_half_length, self.player.position)
            )
            self.move_direction *= -1.0

    def _update_enemies(self, tick: float) -> int:
        defeated = 0
        survivors: List[EnemyState] = []
        for enemy in self.enemies:
            direction = -1.0 if enemy.position > self.player.position else 1.0
            enemy.position += direction * enemy.archetype.speed * tick
            if enemy.health > 0:
                survivors.append(enemy)
            else:
                defeated += 1
                self.enemies_defeated += 1
        self.enemies = survivors
        return defeated

    def _handle_combat(self, tick: float) -> None:
        # Resolve automatic weapon fire.
        if self.player.fire_timer <= 0.0 and self.enemies:
            target = min(self.enemies, key=lambda e: abs(e.position - self.player.position))
            target.health -= self.player.damage_per_shot
            self.player.fire_timer = 1.0 / max(0.1, self.player.fire_rate)
            self.events.append(f"Player struck {target.name}")
            if target.health <= 0:
                self._collect_soul_shard(target)
                self.enemies_defeated += 1

        # Resolve collisions.
        survivors: List[EnemyState] = []
        for enemy in self.enemies:
            if abs(enemy.position - self.player.position) <= 0.3 and enemy.health > 0:
                self.player.health -= enemy.archetype.damage
                self.events.append(f"Player took {enemy.archetype.damage} damage from {enemy.name}")
                if self.player.health <= 0:
                    self.player.health = 0
                # enemy is defeated upon impact
                self._collect_soul_shard(enemy)
                self.enemies_defeated += 1
            else:
                survivors.append(enemy)
        self.enemies = survivors

    def _collect_soul_shard(self, enemy: EnemyState) -> None:
        self.soul_shards += 1
        self.player.experience += enemy.archetype.xp_reward
        self.events.append(f"Collected soul shard from {enemy.name}")

    def _handle_level_up(self) -> None:
        curve = self.config.experience_curve
        leveled = False
        while True:
            next_level_index = min(len(curve) - 1, self.player.level)
            required = curve[next_level_index]
            if self.player.experience < required:
                break
            self.player.level += 1
            leveled = True
            self.events.append(f"Hunter reached level {self.player.level}")
            # Spend the experience required for the level-up so that we do not
            # repeatedly re-trigger the same tier and get stuck in an infinite
            # loop once the curve caps out.
            self.player.experience = max(0.0, self.player.experience - required)
            upgrade = self._choose_upgrade()
            if upgrade == "Damage Boost":
                self.player.damage_bonus += self.config.damage_upgrade_bonus
            else:
                self.player.fire_rate_bonus += self.config.fire_rate_bonus
            self.player.upgrade_history.append(upgrade)
            self.events.append(f"Applied upgrade: {upgrade}")

        if leveled:
            # Prevent runaway leveling when the curve is exhausted.
            self.player.level = min(self.player.level, len(curve))

    def _choose_upgrade(self) -> str:
        if "Damage Boost" not in self.player.upgrade_history:
            return "Damage Boost"
        return "Rapid Fire"


def run_mvp_simulation(
    *, seed: Optional[int] = None, config: Optional[MvpConfig] = None
) -> MvpReport:
    """Execute a single MVP simulation and return the resulting report."""

    cfg = config or MvpConfig()
    rng = random.Random(seed)
    seed_value = seed if seed is not None else rng.randrange(1 << 30)
    simulation = MvpSimulation(cfg, rng, seed_value)
    return simulation.run()


def run_mvp_with_snapshots(
    *, seed: Optional[int] = None, config: Optional[MvpConfig] = None
) -> Tuple[MvpReport, Sequence[MvpFrameSnapshot]]:
    """Execute the MVP simulation while capturing per-tick snapshots."""

    cfg = config or MvpConfig()
    rng = random.Random(seed)
    seed_value = seed if seed is not None else rng.randrange(1 << 30)
    simulation = MvpSimulation(cfg, rng, seed_value)
    snapshots: List[MvpFrameSnapshot] = []
    tick = cfg.tick_rate
    while simulation.elapsed < cfg.duration and simulation.player.health > 0:
        snapshots.append(simulation.step(tick))
    report = simulation.build_report()
    return report, tuple(snapshots)


DEFAULT_SUMMARY_EVENT_COUNT = 15


def _format_report(report: MvpReport) -> str:
    enemies = ", ".join(f"{kind}: {count}" for kind, count in report.enemy_type_counts.items())
    upgrades = ", ".join(report.upgrades_applied) if report.upgrades_applied else "None"
    status = "Survived" if report.survived else "Fallen"
    lines = [
        "Nightfall Survivors MVP Run",
        f"Seed: {report.seed}",
        f"Outcome: {status}",
        f"Duration: {report.duration:.1f}s",
        f"Final Health: {report.final_health:.1f}",
        f"Enemies Defeated: {report.enemies_defeated}",
        f"Enemy Mix: {enemies}",
        f"Level Reached: {report.level_reached}",
        f"Soul Shards Collected: {report.soul_shards}",
        f"Upgrades Applied: {upgrades}",
        f"Dashes Performed: {report.dash_count}",
    ]
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry-point for exercising the MVP simulation."""

    parser = argparse.ArgumentParser(description="Run the Nightfall Survivors MVP simulation.")
    parser.add_argument("--seed", type=int, help="Random seed to make the run deterministic.")
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Override the default duration (seconds).",
    )
    parser.add_argument(
        "--tick",
        type=float,
        default=None,
        help="Simulation tick rate in seconds.",
    )
    parser.add_argument("--summary", action="store_true", help="Print summary details after the run.")
    parser.add_argument(
        "--events",
        type=int,
        default=None,
        help=(
            "Number of event log entries to include when --summary is used. "
            "Defaults to 15 and accepts 0 to skip the event log output."
        ),
    )

    args = parser.parse_args(argv)

    config = MvpConfig(
        duration=args.duration if args.duration is not None else MvpConfig.duration,
        tick_rate=args.tick if args.tick is not None else MvpConfig.tick_rate,
    )
    if args.events is not None and args.events < 0:
        parser.error("--events must be zero or a positive integer")

    report = run_mvp_simulation(seed=args.seed, config=config)
    print(_format_report(report))

    if args.summary:
        print()
        events_to_show = args.events if args.events is not None else DEFAULT_SUMMARY_EVENT_COUNT
        if events_to_show == 0:
            print("Event Log omitted by request.")
        else:
            print(f"Event Log (first {events_to_show} events):")
            for line in report.events[:events_to_show]:
                print(f"  - {line}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())

