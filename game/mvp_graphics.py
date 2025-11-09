"""Graphical facade for visualising MVP simulation runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from .audio import AudioEngine, AudioFrame
from .graphics import Camera, GraphicsEngine, RenderFrame, SceneNode
from .graphics_assets import load_asset_manifest
from .mvp import MvpConfig, MvpFrameSnapshot, MvpReport, run_mvp_with_snapshots


Vector2 = Tuple[float, float]


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
    health_ui_sprite: str = "sprites/ui/health_orb"
    experience_ui_sprite: str = "sprites/ui/experience_bar"
    soul_ui_sprite: str = "sprites/ui/soul_counter"
    dash_ready_effect_sprite: str = "sprites/effects/dash_trail"
    level_up_effect_sprite: str = "sprites/effects/level_up_pulse"
    ui_health_position: Vector2 = (96.0, 72.0)
    ui_experience_position: Vector2 = (360.0, 72.0)
    ui_soul_position: Vector2 = (1184.0, 72.0)
    ui_scale: float = 1.0
    ui_layer: str = "ui"
    level_up_effect_layer: str = "ui"
    level_up_effect_duration: float = 1.0


@dataclass(frozen=True)
class MvpVisualizationResult:
    """Result produced by :class:`MvpVisualizer`."""

    report: MvpReport
    frames: Sequence[RenderFrame]
    audio_frames: Sequence[AudioFrame]


ASSET_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "graphics_assets" / "manifest.json"
)


def bootstrap_graphics(engine: Optional[GraphicsEngine] = None) -> GraphicsEngine:
    """Load the asset manifest and apply it to ``engine``."""

    target = engine or GraphicsEngine()
    manifest = load_asset_manifest(ASSET_MANIFEST_PATH)
    manifest.apply(target, replace_existing=True, update_viewport=True)
    return target


class MvpVisualizer:
    """Bridge that converts MVP simulation snapshots into render frames."""

    def __init__(
        self,
        *,
        graphics: Optional[GraphicsEngine] = None,
        audio: Optional[AudioEngine] = None,
        settings: Optional[MvpVisualSettings] = None,
    ) -> None:
        self.graphics = graphics or bootstrap_graphics()
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

        if snapshot.dash_ready:
            effect_offset = -settings.player_scale * 24.0
            yield SceneNode(
                id=f"player_dash_ready_{snapshot.time:.2f}",
                position=((snapshot.player_position * unit_scale) + effect_offset, lane_y),
                layer=settings.player_layer,
                sprite_id=settings.dash_ready_effect_sprite,
                scale=settings.player_scale * 1.2,
                opacity=0.45,
                metadata={"kind": "vfx", "source": "dash_ready"},
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

        viewport = self.graphics.viewport
        yield from self._build_ui_nodes(snapshot, viewport)
        yield from self._build_level_up_effects(snapshot, viewport)

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

    def _build_ui_nodes(
        self, snapshot: MvpFrameSnapshot, viewport: Tuple[int, int]
    ) -> Iterable[SceneNode]:
        settings = self.settings
        health_ratio = 0.0
        if snapshot.player_max_health > 0:
            health_ratio = max(
                0.0, min(1.0, snapshot.player_health / snapshot.player_max_health)
            )

        xp_ratio = 0.0
        if snapshot.next_level_experience > 0:
            xp_ratio = max(
                0.0, min(1.0, snapshot.player_experience / snapshot.next_level_experience)
            )

        yield SceneNode(
            id="ui.health",
            position=self._ui_anchor(settings.ui_health_position, viewport),
            layer=settings.ui_layer,
            sprite_id=settings.health_ui_sprite,
            scale=settings.ui_scale,
            parallax=1.0,
            metadata={
                "kind": "ui.health",
                "value": snapshot.player_health,
                "max": snapshot.player_max_health,
                "ratio": health_ratio,
            },
        )

        yield SceneNode(
            id="ui.experience",
            position=self._ui_anchor(settings.ui_experience_position, viewport),
            layer=settings.ui_layer,
            sprite_id=settings.experience_ui_sprite,
            scale=settings.ui_scale,
            parallax=1.0,
            metadata={
                "kind": "ui.experience",
                "value": snapshot.player_experience,
                "next_level": snapshot.next_level_experience,
                "level": snapshot.player_level,
                "ratio": xp_ratio,
            },
        )

        yield SceneNode(
            id="ui.souls",
            position=self._ui_anchor(settings.ui_soul_position, viewport),
            layer=settings.ui_layer,
            sprite_id=settings.soul_ui_sprite,
            scale=settings.ui_scale,
            parallax=1.0,
            metadata={
                "kind": "ui.collectible",
                "soul_shards": snapshot.soul_shards,
            },
        )

    def _build_level_up_effects(
        self, snapshot: MvpFrameSnapshot, viewport: Tuple[int, int]
    ) -> Iterable[SceneNode]:
        if not snapshot.events:
            return ()

        if not any("level" in event.lower() for event in snapshot.events):
            return ()

        settings = self.settings
        return (
            SceneNode(
                id=f"ui.level_up.{snapshot.time:.2f}",
                position=self._ui_anchor(settings.ui_experience_position, viewport),
                layer=settings.level_up_effect_layer,
                sprite_id=settings.level_up_effect_sprite,
                scale=settings.ui_scale * 1.1,
                opacity=0.85,
                parallax=1.0,
                metadata={
                    "kind": "vfx",
                    "event": "level_up",
                    "time": snapshot.time,
                    "duration": settings.level_up_effect_duration,
                },
            ),
        )

    @staticmethod
    def _ui_anchor(offset: Vector2, viewport: Tuple[int, int]) -> Vector2:
        half_w = viewport[0] * 0.5
        half_h = viewport[1] * 0.5
        return (-half_w + offset[0], -half_h + offset[1])


__all__ = [
    "MvpVisualSettings",
    "MvpVisualizationResult",
    "MvpVisualizer",
    "bootstrap_graphics",
]
