"""Graphical facade for visualising MVP simulation runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from .audio import AudioEngine, AudioFrame
from .graphics import Camera, GraphicsEngine, RenderFrame, SceneNode
from .mvp import MvpConfig, MvpFrameSnapshot, MvpReport, run_mvp_with_snapshots


@dataclass(frozen=True)
class MvpVisualSettings:
    """Configuration used when translating snapshots into scene nodes."""

    unit_scale: float = 96.0
    lane_y: float = 0.0
    player_layer: str = "actors"
    enemy_layer: str = "actors"
    background_layer: str = "background"
    ui_layer: str = "ui"
    background_sprite: str = "placeholders/background"
    player_sprite: str = "placeholders/player"
    enemy_sprite: str = "placeholders/enemy"
    player_scale: float = 1.0
    enemy_scale: float = 1.0
    enemy_row_height: float = -48.0


@dataclass(frozen=True)
class MvpVisualizationResult:
    """Result produced by :class:`MvpVisualizer`."""

    report: MvpReport
    frames: Sequence[RenderFrame]
    audio_frames: Sequence[AudioFrame]


class MvpVisualizer:
    """Bridge that converts MVP simulation snapshots into render frames."""

    def __init__(
        self,
        *,
        graphics: Optional[GraphicsEngine] = None,
        audio: Optional[AudioEngine] = None,
        settings: Optional[MvpVisualSettings] = None,
    ) -> None:
        self.graphics = graphics or GraphicsEngine()
        self.audio = audio or AudioEngine()
        self.settings = settings or MvpVisualSettings()

    def run(
        self,
        *,
        seed: Optional[int] = None,
        config: Optional[MvpConfig] = None,
        camera: Optional[Camera] = None,
    ) -> MvpVisualizationResult:
        """Execute the simulation and return renderable frames."""

        cfg = config or MvpConfig()
        report, snapshots = run_mvp_with_snapshots(seed=seed, config=cfg)

        viewport_camera = camera or Camera(viewport=self.graphics.viewport)
        frames = self._build_frames(snapshots, camera=viewport_camera)
        audio_frames = self._build_audio_frames(snapshots)
        return MvpVisualizationResult(
            report=report,
            frames=tuple(frames),
            audio_frames=tuple(audio_frames),
        )

    def _build_frames(
        self,
        snapshots: Sequence[MvpFrameSnapshot],
        *,
        camera: Camera,
    ) -> List[RenderFrame]:
        frames: List[RenderFrame] = []
        for snapshot in snapshots:
            nodes = list(self.build_scene_nodes(snapshot))
            messages = self._messages_for_snapshot(snapshot)
            frames.append(
                self.graphics.build_frame(
                    nodes,
                    camera=camera,
                    time=snapshot.time,
                    messages=messages,
                )
            )
        return frames

    def _build_audio_frames(
        self, snapshots: Sequence[MvpFrameSnapshot]
    ) -> List[AudioFrame]:
        frames: List[AudioFrame] = []
        for snapshot in snapshots:
            frames.append(
                self.audio.build_frame(snapshot.audio_events, time=snapshot.time)
            )
        return frames

    def build_scene_nodes(self, snapshot: MvpFrameSnapshot) -> Iterable[SceneNode]:
        settings = self.settings
        unit_scale = settings.unit_scale
        lane_y = settings.lane_y

        yield SceneNode(
            id="background",
            position=(0.0, lane_y),
            layer=settings.background_layer,
            sprite_id=settings.background_sprite,
            metadata={"kind": "background"},
        )

        yield SceneNode(
            id="player",
            position=(snapshot.player_position * unit_scale, lane_y),
            layer=settings.player_layer,
            sprite_id=settings.player_sprite,
            scale=settings.player_scale,
            metadata={
                "kind": "player",
                "health": snapshot.player_health,
                "max_health": snapshot.player_max_health,
                "level": snapshot.player_level,
                "experience": snapshot.player_experience,
                "next_level_experience": snapshot.next_level_experience,
                "dash_ready": snapshot.dash_ready,
                "dash_cooldown": snapshot.dash_cooldown,
                "fire_cooldown": snapshot.fire_cooldown,
                "soul_shards": snapshot.soul_shards,
                "enemies_defeated": snapshot.enemies_defeated,
            },
        )

        for index, enemy in enumerate(snapshot.enemies):
            enemy_y = lane_y + settings.enemy_row_height * (index % 3)
            yield SceneNode(
                id=f"enemy_{enemy.id}",
                position=(enemy.position * unit_scale, enemy_y),
                layer=settings.enemy_layer,
                sprite_id=settings.enemy_sprite,
                scale=settings.enemy_scale,
                metadata={
                    "kind": "enemy",
                    "name": enemy.name,
                    "health": enemy.health,
                    "max_health": enemy.max_health,
                    "damage": enemy.damage,
                    "speed": enemy.speed,
                    "xp_reward": enemy.xp_reward,
                },
            )

    def _messages_for_snapshot(self, snapshot: MvpFrameSnapshot) -> Sequence[str]:
        lines = list(snapshot.events)
        lines.append(
            "Health: {:.0f}/{:.0f} | Level {}".format(
                snapshot.player_health,
                snapshot.player_max_health,
                snapshot.player_level,
            )
        )
        lines.append(
            "Soul Shards: {} | Defeated: {}".format(
                snapshot.soul_shards, snapshot.enemies_defeated
            )
        )
        return tuple(lines)


__all__ = [
    "MvpVisualSettings",
    "MvpVisualizationResult",
    "MvpVisualizer",
]
