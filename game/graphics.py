"""Rendering abstraction for bridging the prototype to a real graphics stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


Vector2 = Tuple[float, float]
Color = Tuple[int, int, int]


@dataclass(frozen=True)
class Sprite:
    """Metadata describing how to render a single sprite frame."""

    id: str
    texture: str
    size: Tuple[int, int]
    pivot: Vector2 = (0.5, 0.5)
    tint: Optional[Color] = None


@dataclass(frozen=True)
class AnimationFrame:
    """A single frame within an animation clip."""

    sprite_id: str
    duration: float


@dataclass(frozen=True)
class AnimationClip:
    """Describes a looping sprite animation."""

    id: str
    frames: Sequence[AnimationFrame]
    loop: bool = True

    def total_duration(self) -> float:
        return sum(frame.duration for frame in self.frames)

    def sprite_for_time(self, time: float) -> str:
        """Return the sprite id that should be displayed at ``time`` seconds."""

        if not self.frames:
            raise ValueError("animation clip must contain at least one frame")

        total = self.total_duration()
        if total <= 0:
            return self.frames[-1].sprite_id

        if self.loop:
            time = time % total
        else:
            time = min(time, total - 1e-6)

        elapsed = 0.0
        for frame in self.frames:
            elapsed += frame.duration
            if time < elapsed or frame is self.frames[-1]:
                return frame.sprite_id
        return self.frames[-1].sprite_id


@dataclass(frozen=True)
class LayerSettings:
    """Rendering layer configuration."""

    name: str
    z_index: int
    parallax: float = 1.0
    scroll: Vector2 = (0.0, 0.0)


@dataclass(frozen=True)
class Camera:
    """Camera information used to project world coordinates into screen space."""

    position: Vector2 = (0.0, 0.0)
    viewport: Tuple[int, int] = (1280, 720)
    zoom: float = 1.0


@dataclass
class SceneNode:
    """A logical item that should be turned into a render instruction."""

    id: str
    position: Vector2
    layer: str
    sprite_id: Optional[str] = None
    animation_id: Optional[str] = None
    scale: float = 1.0
    rotation: float = 0.0
    flip_x: bool = False
    flip_y: bool = False
    parallax: Optional[float] = None
    metadata: MutableMapping[str, object] = field(default_factory=dict)

    @property
    def kind(self) -> Optional[str]:
        value = self.metadata.get("kind")
        return str(value) if value is not None else None


@dataclass(frozen=True)
class RenderInstruction:
    """Result of evaluating a scene graph for a single sprite."""

    node_id: str
    sprite: Sprite
    position: Vector2
    scale: float
    rotation: float
    flip_x: bool
    flip_y: bool
    layer: str
    z_index: int
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class RenderFrame:
    """All render instructions for a frame."""

    time: float
    viewport: Tuple[int, int]
    instructions: Sequence[RenderInstruction]
    messages: Sequence[str] = ()


class GraphicsEngine:
    """Lightweight renderer facade that prepares data for a graphics front end."""

    def __init__(
        self,
        *,
        viewport: Tuple[int, int] = (1280, 720),
        layers: Optional[Sequence[LayerSettings]] = None,
    ) -> None:
        self._viewport = viewport
        self._sprites: Dict[str, Sprite] = {}
        self._animations: Dict[str, AnimationClip] = {}
        self._layers: Dict[str, LayerSettings] = {}
        self._fallback_sprite_id = "__fallback__"
        self._placeholders: Dict[str, str] = {}

        self.register_sprite(
            Sprite(
                id=self._fallback_sprite_id,
                texture="sprites/missing.png",
                size=(64, 64),
                pivot=(0.5, 0.5),
            )
        )

        self.register_sprite(
            Sprite(
                id="placeholders/player",
                texture="sprites/player_placeholder.png",
                size=(96, 96),
            )
        )
        self.register_sprite(
            Sprite(
                id="placeholders/enemy",
                texture="sprites/enemy_placeholder.png",
                size=(96, 96),
            )
        )
        self.register_sprite(
            Sprite(
                id="placeholders/projectile",
                texture="sprites/projectile_placeholder.png",
                size=(32, 32),
            )
        )
        self.register_sprite(
            Sprite(
                id="placeholders/background",
                texture="sprites/background_placeholder.png",
                size=(1280, 720),
                pivot=(0.0, 0.0),
            )
        )

        self.register_placeholder("player", "placeholders/player")
        self.register_placeholder("enemy", "placeholders/enemy")
        self.register_placeholder("projectile", "placeholders/projectile")
        self.register_placeholder("background", "placeholders/background")

        default_layers = layers or (
            LayerSettings("background", z_index=0, parallax=0.35),
            LayerSettings("midground", z_index=5, parallax=0.7),
            LayerSettings("actors", z_index=10, parallax=1.0),
            LayerSettings("projectiles", z_index=12, parallax=1.0),
            LayerSettings("foreground", z_index=18, parallax=1.15),
            LayerSettings("ui", z_index=100, parallax=0.0),
        )
        for layer in default_layers:
            self.register_layer(layer)

    @property
    def viewport(self) -> Tuple[int, int]:
        return self._viewport

    def register_sprite(self, sprite: Sprite) -> None:
        self._sprites[sprite.id] = sprite

    def register_animation(self, clip: AnimationClip) -> None:
        if not clip.frames:
            raise ValueError("animation clip must have at least one frame")
        self._animations[clip.id] = clip

    def register_layer(self, layer: LayerSettings) -> None:
        self._layers[layer.name] = layer

    def register_placeholder(self, kind: str, sprite_id: str) -> None:
        self._placeholders[kind] = sprite_id

    def sprite(self, sprite_id: str) -> Sprite:
        return self._sprites[sprite_id]

    def build_frame(
        self,
        nodes: Iterable[SceneNode],
        *,
        camera: Optional[Camera] = None,
        time: float = 0.0,
        messages: Optional[Sequence[str]] = None,
    ) -> RenderFrame:
        camera = camera or Camera(viewport=self._viewport)
        instructions: List[RenderInstruction] = []

        for order, node in enumerate(nodes):
            sprite = self._resolve_sprite(node, time)
            if sprite is None:
                continue

            layer = self._layers.get(node.layer)
            if layer is None:
                layer = LayerSettings(name=node.layer, z_index=50, parallax=1.0)
                self.register_layer(layer)

            parallax = node.parallax if node.parallax is not None else layer.parallax
            screen_x = (node.position[0] - camera.position[0]) * camera.zoom * parallax
            screen_y = (node.position[1] - camera.position[1]) * camera.zoom * parallax
            screen_x += camera.viewport[0] * 0.5
            screen_y += camera.viewport[1] * 0.5

            instruction = RenderInstruction(
                node_id=node.id,
                sprite=sprite,
                position=(screen_x, screen_y),
                scale=node.scale * camera.zoom,
                rotation=node.rotation,
                flip_x=node.flip_x,
                flip_y=node.flip_y,
                layer=node.layer,
                z_index=layer.z_index,
                metadata=dict(node.metadata),
            )
            instructions.append(instruction)

        instructions.sort(key=lambda inst: (inst.z_index, inst.layer, inst.node_id))
        return RenderFrame(
            time=time,
            viewport=camera.viewport,
            instructions=tuple(instructions),
            messages=tuple(messages or ()),
        )

    def _resolve_sprite(self, node: SceneNode, time: float) -> Optional[Sprite]:
        sprite_id = node.sprite_id
        if node.animation_id:
            clip = self._animations.get(node.animation_id)
            if clip is None:
                raise KeyError(f"unknown animation clip '{node.animation_id}'")
            sprite_id = clip.sprite_for_time(time)

        if sprite_id and sprite_id in self._sprites:
            return self._sprites[sprite_id]

        placeholder_key = node.kind or ""
        if placeholder_key in self._placeholders:
            sprite_id = self._placeholders[placeholder_key]
            return self._sprites.get(sprite_id, self._sprites[self._fallback_sprite_id])

        return self._sprites[self._fallback_sprite_id]
