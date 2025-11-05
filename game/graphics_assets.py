"""Asset management helpers for the 2D graphics engine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence, Tuple

from .graphics import Color, GraphicsEngine, LayerSettings, Sprite

Vector2 = Tuple[float, float]


@dataclass(frozen=True)
class LayerDefinition:
    """Description of a render layer expected by the asset manifest."""

    name: str
    z_index: int
    parallax: float = 1.0
    scroll: Vector2 = (0.0, 0.0)

    def to_layer_settings(self) -> LayerSettings:
        return LayerSettings(name=self.name, z_index=self.z_index, parallax=self.parallax, scroll=self.scroll)


@dataclass(frozen=True)
class SpriteDefinition:
    """Serializable sprite specification stored on disk."""

    id: str
    texture: str
    size: Tuple[int, int]
    pivot: Vector2
    tint: Color | None = None
    display_name: str | None = None
    role: str = ""
    description: str = ""
    palette: Tuple[str, ...] = ()
    mood: str = ""
    lighting: str = ""
    art_style: str = ""
    notes: Tuple[str, ...] = ()
    tags: Tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "SpriteDefinition":
        def _tuple(name: str, fallback: Sequence[object] = ()) -> Tuple[object, ...]:
            value = payload.get(name, fallback)
            if value is None:
                return tuple()
            return tuple(value)  # type: ignore[arg-type]

        tint_value = payload.get("tint")
        tint: Color | None
        if tint_value is None:
            tint = None
        else:
            components = tuple(int(component) for component in tint_value)  # type: ignore[arg-type]
            tint = (components[0], components[1], components[2])  # type: ignore[assignment]

        return cls(
            id=str(payload["id"]),
            texture=str(payload["texture"]),
            size=(int(payload["size"][0]), int(payload["size"][1])),  # type: ignore[index]
            pivot=(float(payload["pivot"][0]), float(payload["pivot"][1])),  # type: ignore[index]
            tint=tint,
            display_name=payload.get("display_name") or None,
            role=str(payload.get("role", "")),
            description=str(payload.get("description", "")),
            palette=tuple(str(entry) for entry in _tuple("palette")),
            mood=str(payload.get("mood", "")),
            lighting=str(payload.get("lighting", "")),
            art_style=str(payload.get("art_style", "")),
            notes=tuple(str(entry) for entry in _tuple("notes")),
            tags=tuple(str(entry) for entry in _tuple("tags")),
        )

    def to_sprite(self) -> Sprite:
        return Sprite(
            id=self.id,
            texture=self.texture,
            size=self.size,
            pivot=self.pivot,
            tint=self.tint,
            display_name=self.display_name,
            role=self.role,
            description=self.description,
            palette=self.palette,
            mood=self.mood,
            lighting=self.lighting,
            art_style=self.art_style,
            notes=self.notes,
            tags=self.tags,
        )

    def texture_path(self, root: Path) -> Path:
        return root / self.texture


@dataclass(frozen=True)
class SpriteAssetManifest:
    """Container representing the JSON manifest stored on disk."""

    viewport: Tuple[int, int]
    sprites: Tuple[SpriteDefinition, ...]
    placeholders: Mapping[str, str]
    layers: Tuple[LayerDefinition, ...]

    def apply(
        self,
        engine: GraphicsEngine,
        *,
        replace_existing: bool = False,
        update_viewport: bool = False,
    ) -> None:
        """Register sprites, layers, and placeholders with ``engine``."""

        if update_viewport:
            engine.set_viewport(self.viewport)

        for layer in self.layers:
            engine.register_layer(layer.to_layer_settings())

        for sprite in self.sprites:
            if not replace_existing:
                try:
                    engine.sprite(sprite.id)
                    continue
                except KeyError:
                    pass
            engine.register_sprite(sprite.to_sprite())

        existing_placeholders: Mapping[str, str] = {}
        if not replace_existing:
            existing_placeholders = engine.build_manifest().placeholders

        for kind, sprite_id in self.placeholders.items():
            if replace_existing or kind not in existing_placeholders:
                engine.register_placeholder(kind, sprite_id)

    def validate_assets(self, asset_root: Path) -> Tuple[str, ...]:
        """Return warnings about missing or mismatched sprite textures."""

        warnings: list[str] = []
        for definition in self.sprites:
            path = definition.texture_path(asset_root)
            if not path.exists():
                warnings.append(f"Missing texture for {definition.id!r}: {path}")
                continue
            try:
                width, height = read_texture_dimensions(path)
            except ValueError as exc:
                warnings.append(f"Invalid texture descriptor for {definition.id!r}: {path} ({exc})")
                continue
            expected_width, expected_height = definition.size
            if (width, height) != (expected_width, expected_height):
                warnings.append(
                    f"Texture size mismatch for {definition.id!r}: expected {expected_width}x{expected_height}, found {width}x{height}"
                )
        return tuple(warnings)


def read_png_dimensions(path: Path) -> Tuple[int, int]:
    """Read the width and height stored in a PNG file."""

    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG file")
        length_bytes = handle.read(4)
        if len(length_bytes) != 4:
            raise ValueError("corrupt PNG length header")
        chunk_length = int.from_bytes(length_bytes, "big")
        chunk_type = handle.read(4)
        if chunk_type != b"IHDR":
            raise ValueError("IHDR chunk not found")
        ihdr_data = handle.read(chunk_length)
        if len(ihdr_data) != chunk_length:
            raise ValueError("truncated IHDR chunk")
        width = int.from_bytes(ihdr_data[0:4], "big")
        height = int.from_bytes(ihdr_data[4:8], "big")
        return width, height


def read_texture_descriptor_dimensions(path: Path) -> Tuple[int, int]:
    """Return dimensions stored in a JSON texture descriptor."""

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"invalid JSON payload: {exc}") from exc

    try:
        width = int(payload["width"])
        height = int(payload["height"])
    except KeyError as exc:
        raise ValueError("descriptor missing width/height") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("descriptor width/height must be integers") from exc

    return width, height


def read_texture_dimensions(path: Path) -> Tuple[int, int]:
    """Return sprite dimensions for either PNGs or JSON descriptors."""

    suffixes = [suffix.lower() for suffix in path.suffixes]
    suffix = path.suffix.lower()
    if suffixes[-2:] == [".texture", ".json"] or suffix == ".json":
        return read_texture_descriptor_dimensions(path)
    if suffix == ".png":
        return read_png_dimensions(path)
    raise ValueError("unsupported texture format; expected .png or .texture.json")


def load_asset_manifest(path: Path | str) -> SpriteAssetManifest:
    """Load a sprite manifest JSON file from ``path``."""

    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text())

    viewport_data = payload.get("viewport", [1280, 720])
    viewport = (int(viewport_data[0]), int(viewport_data[1]))

    sprites = tuple(SpriteDefinition.from_dict(entry) for entry in payload.get("sprites", ()))

    placeholder_mapping: MutableMapping[str, str] = {}
    for kind, sprite_id in payload.get("placeholders", {}).items():
        placeholder_mapping[str(kind)] = str(sprite_id)

    layers = []
    for name, entry in payload.get("layers", {}).items():
        parallax = float(entry.get("parallax", 1.0))
        scroll_values = entry.get("scroll", (0.0, 0.0))
        scroll = (float(scroll_values[0]), float(scroll_values[1]))  # type: ignore[index]
        layers.append(
            LayerDefinition(
                name=str(name),
                z_index=int(entry.get("z_index", 0)),
                parallax=parallax,
                scroll=scroll,
            )
        )

    return SpriteAssetManifest(
        viewport=viewport,
        sprites=sprites,
        placeholders=dict(placeholder_mapping),
        layers=tuple(layers),
    )


def ensure_asset_layout(asset_root: Path, manifest: SpriteAssetManifest) -> None:
    """Create folders needed to store sprite textures as described by ``manifest``."""

    asset_root = Path(asset_root)
    for definition in manifest.sprites:
        definition.texture_path(asset_root).parent.mkdir(parents=True, exist_ok=True)


__all__ = [
    "LayerDefinition",
    "SpriteDefinition",
    "SpriteAssetManifest",
    "ensure_asset_layout",
    "load_asset_manifest",
    "read_png_dimensions",
    "read_texture_descriptor_dimensions",
    "read_texture_dimensions",
]
