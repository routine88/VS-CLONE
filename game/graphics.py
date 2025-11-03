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
    display_name: Optional[str] = None
    role: str = ""
    description: str = ""
    palette: Tuple[str, ...] = ()
    mood: str = ""
    lighting: str = ""
    art_style: str = ""
    notes: Tuple[str, ...] = ()
    tags: Tuple[str, ...] = ()

    def brief(self) -> "SpriteBrief":
        """Return a :class:`SpriteBrief` suitable for asset planning documents."""

        return SpriteBrief(
            id=self.id,
            name=self.display_name or self.id,
            texture=self.texture,
            size=self.size,
            pivot=self.pivot,
            purpose=self.role,
            description=self.description,
            palette=self.palette,
            mood=self.mood,
            lighting=self.lighting,
            art_style=self.art_style,
            notes=self.notes,
            tags=self.tags,
        )


@dataclass(frozen=True)
class SpriteBrief:
    """Human-friendly description of an art asset requirement."""

    id: str
    name: str
    texture: str
    size: Tuple[int, int]
    pivot: Vector2
    purpose: str
    description: str
    palette: Tuple[str, ...]
    mood: str
    lighting: str
    art_style: str
    notes: Tuple[str, ...]
    tags: Tuple[str, ...]

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "texture": self.texture,
            "size": list(self.size),
            "pivot": list(self.pivot),
            "purpose": self.purpose,
            "description": self.description,
            "palette": list(self.palette),
            "mood": self.mood,
            "lighting": self.lighting,
            "art_style": self.art_style,
            "notes": list(self.notes),
            "tags": list(self.tags),
        }


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


@dataclass(frozen=True)
class GraphicsManifest:
    """Snapshot of registered graphics resources."""

    viewport: Tuple[int, int]
    sprites: Mapping[str, Sprite]
    placeholders: Mapping[str, str]
    layers: Mapping[str, LayerSettings]

    def to_dict(self) -> Dict[str, object]:
        """Convert the manifest to JSON-serialisable primitives."""

        return {
            "viewport": list(self.viewport),
            "sprites": {
                sprite_id: {
                    "texture": sprite.texture,
                    "size": list(sprite.size),
                    "pivot": list(sprite.pivot),
                    "tint": list(sprite.tint) if sprite.tint is not None else None,
                    "display_name": sprite.display_name,
                    "role": sprite.role,
                    "description": sprite.description,
                    "palette": list(sprite.palette),
                    "mood": sprite.mood,
                    "lighting": sprite.lighting,
                    "art_style": sprite.art_style,
                    "notes": list(sprite.notes),
                    "tags": list(sprite.tags),
                    "brief": sprite.brief().to_dict(),
                }
                for sprite_id, sprite in self.sprites.items()
            },
            "placeholders": dict(self.placeholders),
            "layers": {
                layer_id: {
                    "name": layer.name,
                    "z_index": layer.z_index,
                    "parallax": layer.parallax,
                    "scroll": list(layer.scroll),
                }
                for layer_id, layer in self.layers.items()
            },
        }


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

        seed_sprites = (
            Sprite(
                id=self._fallback_sprite_id,
                texture="sprites/missing.texture.json",
                size=(64, 64),
                pivot=(0.5, 0.5),
                display_name="Missing Asset Placeholder",
                role="Fallback / debug",
                description="High-contrast error tile shown whenever an expected sprite is absent.",
                palette=("#FF00FF - neon magenta", "#000000 - absolute black"),
                mood="Utility glitch",
                lighting="Flat emission, no shading.",
                art_style="Pixel-perfect checkerboard.",
                notes=("Should be unmistakable as an error state.",),
                tags=("placeholder", "debug"),
            ),
            Sprite(
                id="placeholders/player",
                texture="sprites/player_placeholder.texture.json",
                size=(96, 96),
                display_name="Hunter Vanguard Placeholder",
                role="Player character stand-in",
                description="Agile hunter with arc pistol, cloak fluttering back, facing three-quarter right.",
                palette=(
                    "#5CF1FF - arc energy cyan",
                    "#22252B - charcoal armour",
                    "#F5F2E8 - pale fabric highlight",
                    "#EC9C47 - warm accent trims",
                ),
                mood="Heroic and ready for action.",
                lighting="Strong top-left rim light to emphasise silhouette.",
                art_style="Stylised cel-shaded character illustration.",
                notes=(
                    "Weapon hand forward, muzzle pointing to screen right.",
                    "Cape reads as a separate shape for animation overlap.",
                ),
                tags=("player", "character", "placeholder"),
            ),
            Sprite(
                id="placeholders/enemy",
                texture="sprites/enemy_placeholder.texture.json",
                size=(96, 96),
                display_name="Cultist Brute Placeholder",
                role="Enemy stand-in",
                description="Broad-shouldered cultist with glowing void mask and heavy melee weapon.",
                palette=(
                    "#341A3A - deep violet cloth",
                    "#7E2F8E - saturated magenta armour",
                    "#E6DADA - bone mask glow",
                    "#2B101F - shadow core",
                ),
                mood="Menacing brute",
                lighting="Underlit with purple bounce, subtle top rim.",
                art_style="Stylised cel-shaded silhouette focus.",
                notes=(
                    "Maintain hulking stance distinct from player silhouette.",
                    "Mask glow should read at thumbnail size.",
                ),
                tags=("enemy", "character", "placeholder"),
            ),
            Sprite(
                id="placeholders/projectile",
                texture="sprites/projectile_placeholder.texture.json",
                size=(32, 32),
                display_name="Arc Bolt Placeholder",
                role="Projectile stand-in",
                description="Diamond-shaped energy bolt with trailing sparks moving left to right.",
                palette=(
                    "#A6F3FF - electric cyan core",
                    "#174D73 - dark cyan outline",
                    "#FFFFFF - white highlight",
                ),
                mood="Fast and crackling.",
                lighting="Self-illuminated glow with subtle bloom.",
                art_style="Minimalist VFX sprite with soft edges.",
                notes=("Align long axis horizontally for side-scrolling readability.",),
                tags=("projectile", "vfx", "placeholder"),
            ),
            Sprite(
                id="placeholders/background",
                texture="sprites/background_placeholder.texture.json",
                size=(1280, 720),
                pivot=(0.0, 0.0),
                display_name="Neon Graveyard Backdrop",
                role="Level background",
                description="Layered parallax city of gothic spires with neon signage and misty foreground graves.",
                palette=(
                    "#15181F - midnight blue sky",
                    "#2F3E64 - distant architecture",
                    "#6AD7FF - neon signage",
                    "#4CFFB6 - spectral accent",
                    "#1A0F24 - foreground silhouettes",
                ),
                mood="Moody, supernatural skyline.",
                lighting="Backlit horizon glow with scattered volumetric beams.",
                art_style="Layered painterly matte with crisp silhouettes.",
                notes=(
                    "Deliver as looping slice suitable for horizontal scrolling.",
                    "Foreground graves should have cutout alpha for parallax stacking.",
                ),
                tags=("environment", "background", "parallax"),
            ),
            Sprite(
                id="sprites/ui/health_orb",
                texture="sprites/ui/health_orb.texture.json",
                size=(64, 64),
                display_name="HUD Health Orb",
                role="UI health indicator",
                description="Circular vial with crimson liquid suspended in ornate brass frame and glass shine.",
                palette=(
                    "#C7313F - vibrant blood red",
                    "#571212 - deep burgundy",
                    "#D9B676 - aged brass",
                    "#0A0C10 - near-black background",
                ),
                mood="Urgent survival HUD.",
                lighting="Glowing internal liquid with specular rim and subtle emissive tick marks.",
                art_style="High-fidelity UI illustration with clean transparency.",
                notes=(
                    "Provide layered source if possible: frame, liquid, highlights.",
                    "Alpha background must be perfectly clean for overlay.",
                ),
                tags=("ui", "hud", "health"),
            ),
            Sprite(
                id="sprites/ui/experience_bar",
                texture="sprites/ui/experience_bar.texture.json",
                size=(512, 64),
                pivot=(0.0, 0.5),
                display_name="HUD Experience Bar",
                role="UI progression indicator",
                description="Horizontal bar with ornate frame and inner neon fill mask progressing left to right.",
                palette=(
                    "#2E1A3B - dark frame base",
                    "#8B4CC5 - mystical violet fill",
                    "#F0E6FF - highlight trims",
                    "#1B0F29 - deep shadow",
                ),
                mood="Arcane progression.",
                lighting="Soft inner glow emanating from fill, metallic specular on frame.",
                art_style="Stylised UI with crisp vector-like edges.",
                notes=(
                    "Supply separate alpha mask for animated fill if possible.",
                    "Left edge should align at pixel 0 for layout anchoring.",
                ),
                tags=("ui", "hud", "progression"),
            ),
            Sprite(
                id="sprites/ui/ability_icon_dash",
                texture="sprites/ui/ability_icon_dash.texture.json",
                size=(96, 96),
                display_name="Ability Icon - Dash",
                role="UI ability icon",
                description="Icon depicting motion-blurred boots streaking forward with cyan energy trail.",
                palette=(
                    "#3AF2FF - dash energy",
                    "#133649 - deep teal shadow",
                    "#F7F9FB - highlight streak",
                    "#1A0E24 - vignette background",
                ),
                mood="Kinetic speed.",
                lighting="Directional motion blur with bright leading edge.",
                art_style="Painterly icon with hard-edged rim lights.",
                notes=(
                    "Rounded square canvas with transparent corners.",
                    "Keep icon readable at 48px.",
                ),
                tags=("ui", "icon", "ability"),
            ),
            Sprite(
                id="sprites/effects/dash_trail",
                texture="sprites/effects/dash_trail.texture.json",
                size=(128, 64),
                pivot=(0.2, 0.5),
                display_name="Dash Trail",
                role="Movement VFX",
                description="Elongated energy swoosh tapering to wisps, oriented left-to-right motion blur.",
                palette=(
                    "#4FF7FF - bright cyan core",
                    "#1C5B73 - deep teal edge",
                    "#B9FFFF - soft highlight",
                ),
                mood="Energetic burst",
                lighting="Self-illuminated with slight transparency gradient.",
                art_style="Soft additive VFX sprite.",
                notes=(
                    "Provide three sequential frames fading out for animation.",
                    "Edge feathering should avoid hard pixels.",
                ),
                tags=("vfx", "movement", "dash"),
            ),
            Sprite(
                id="sprites/effects/hit_flash",
                texture="sprites/effects/hit_flash.texture.json",
                size=(96, 96),
                display_name="Hit Flash",
                role="Damage feedback VFX",
                description="Radial burst with jagged spikes and central flash to overlay on struck enemies.",
                palette=(
                    "#FFD75C - golden burst",
                    "#FF9147 - orange impact",
                    "#FFFFFF - intense core",
                    "#4D1A0D - dark rim",
                ),
                mood="Sharp impact",
                lighting="Bright center with fast falloff to transparent edges.",
                art_style="Graphic comic-book style burst.",
                notes=("Two to three frames with diminishing intensity for animation.",),
                tags=("vfx", "impact", "combat"),
            ),
            Sprite(
                id="sprites/effects/soul_pickup",
                texture="sprites/effects/soul_pickup.texture.json",
                size=(80, 80),
                display_name="Soul Shard Pickup",
                role="Collectible VFX",
                description="Floating crystal shard orbiting smaller motes with ethereal glow.",
                palette=(
                    "#7FFFD4 - aqua glow",
                    "#3A1C5E - void core",
                    "#C2FFE9 - pale highlights",
                ),
                mood="Mystical reward",
                lighting="Inner glow with subtle pulsing outer aura.",
                art_style="Stylised magical collectible.",
                notes=("Supports looping four-frame twinkle animation.",),
                tags=("collectible", "vfx", "reward"),
            ),
            Sprite(
                id="sprites/environment/barricade_intact",
                texture="sprites/environment/barricade_intact.texture.json",
                size=(192, 128),
                display_name="Gravestone Barricade - Intact",
                role="Breakable obstacle",
                description="Cluster of ruined gravestones bound by arcane chains blocking the lane.",
                palette=(
                    "#5F6B7A - weathered stone",
                    "#1D242C - deep cracks",
                    "#8FF2FF - arcane chain glow",
                    "#2B1A33 - damp earth base",
                ),
                mood="Ancient and oppressive.",
                lighting="Top-down moonlight with subsurface glow in runes.",
                art_style="Painterly environment prop with crisp edges.",
                notes=(
                    "Design to break cleanly into two halves for destruction state.",
                    "Alpha fringe should remain tight for collision accuracy.",
                ),
                tags=("environment", "obstacle", "breakable"),
            ),
            Sprite(
                id="sprites/environment/barricade_broken",
                texture="sprites/environment/barricade_broken.texture.json",
                size=(192, 128),
                display_name="Gravestone Barricade - Broken",
                role="Breakable obstacle debris",
                description="Fragments of gravestones scattered with fading chain energy and dust.",
                palette=(
                    "#515B67 - shattered stone",
                    "#161B22 - deep crevice",
                    "#68D7E8 - dissipating magic",
                    "#B7BEC9 - dust motes",
                ),
                mood="Aftermath of destruction.",
                lighting="Residual glow concentrated near fragments, softer shadows.",
                art_style="Painterly shards with motion hints.",
                notes=("Pairs with intact version; ensure silhouettes align for swap.",),
                tags=("environment", "obstacle", "debris"),
            ),
        )

        for sprite in seed_sprites:
            self.register_sprite(sprite)

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

    def set_viewport(self, viewport: Tuple[int, int]) -> None:
        """Override the active viewport dimensions."""

        self._viewport = viewport

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

    def build_manifest(self) -> GraphicsManifest:
        """Return a snapshot of all registered sprites, placeholders, and layers."""

        return GraphicsManifest(
            viewport=self._viewport,
            sprites=dict(self._sprites),
            placeholders=dict(self._placeholders),
            layers=dict(self._layers),
        )

    def build_sprite_briefs(self) -> Sequence[SpriteBrief]:
        """Return an ordered collection of :class:`SpriteBrief` entries."""

        return tuple(
            sprite.brief() for sprite in sorted(self._sprites.values(), key=lambda spr: spr.id)
        )

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
