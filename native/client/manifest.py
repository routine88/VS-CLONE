"""Helpers for consuming the graphics manifest in the native client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any, Dict, Tuple

from .dto import SpriteDescriptor

Vector2 = Tuple[float, float]


@dataclass(frozen=True)
class LayerDefinition:
    """Definition of a render layer provided by the content manifest."""

    id: str
    z_index: int
    parallax: float
    scroll: Vector2


@dataclass(frozen=True)
class ManifestSprite:
    """Sprite entry sourced from the graphics manifest."""

    id: str
    texture: str
    size: Tuple[int, int]
    pivot: Vector2
    tint: Tuple[int, int, int] | None
    display_name: str | None
    role: str
    description: str
    palette: Tuple[str, ...]
    mood: str
    lighting: str
    art_style: str
    notes: Tuple[str, ...]
    tags: Tuple[str, ...]
    root: Path

    @property
    def texture_path(self) -> Path:
        return self.root / self.texture

    def to_sprite_descriptor(self) -> SpriteDescriptor:
        return SpriteDescriptor(
            id=self.id,
            texture=str(self.texture_path),
            size=self.size,
            pivot=self.pivot,
            tint=self.tint,
        )


@dataclass(frozen=True)
class GraphicsManifest:
    """Materialised version of ``assets/graphics_assets/manifest.json``."""

    root: Path
    viewport: Tuple[int, int]
    sprites: Dict[str, ManifestSprite]
    placeholders: Dict[str, str]
    layers: Dict[str, LayerDefinition]

    @classmethod
    def from_path(cls, path: Path) -> "GraphicsManifest":
        payload = json.loads(path.read_text())
        root = path.parent
        viewport_payload = payload.get("viewport", (0, 0))
        sprites_payload = payload.get("sprites", [])
        layers_payload = payload.get("layers", {})
        placeholders_payload = payload.get("placeholders", {})

        sprites: Dict[str, ManifestSprite] = {}

        if isinstance(sprites_payload, Mapping):
            sprite_entries = sprites_payload.items()
        else:
            sprite_entries = ((None, entry) for entry in _as_iterable(sprites_payload))

        for explicit_id, entry in sprite_entries:
            if not isinstance(entry, Mapping):
                continue

            sprite_id = entry.get("id", explicit_id)
            if sprite_id is None:
                continue

            texture = entry.get("texture")
            if texture is None:
                continue

            sprite = ManifestSprite(
                id=str(sprite_id),
                texture=str(texture),
                size=_coerce_int_pair(entry.get("size"), default=(0, 0)),
                pivot=_coerce_float_pair(entry.get("pivot"), default=(0.0, 0.0)),
                tint=_optional_tint(entry.get("tint")),
                display_name=entry.get("display_name") or None,
                role=str(entry.get("role", "")),
                description=str(entry.get("description", "")),
                palette=_tuple_of_strings(entry.get("palette")),
                mood=str(entry.get("mood", "")),
                lighting=str(entry.get("lighting", "")),
                art_style=str(entry.get("art_style", "")),
                notes=_tuple_of_strings(entry.get("notes")),
                tags=_tuple_of_strings(entry.get("tags")),
                root=root,
            )
            sprites[sprite.id] = sprite

        layers: Dict[str, LayerDefinition] = {}
        for layer_id, entry in layers_payload.items():
            scroll_payload = entry.get("scroll", (0.0, 0.0))
            layers[layer_id] = LayerDefinition(
                id=layer_id,
                z_index=int(entry.get("z_index", 0)),
                parallax=float(entry.get("parallax", 1.0)),
                scroll=(float(scroll_payload[0]), float(scroll_payload[1])),  # type: ignore[index]
            )

        placeholders = _normalise_placeholders(placeholders_payload)

        return cls(
            root=root,
            viewport=(int(viewport_payload[0]), int(viewport_payload[1])),  # type: ignore[index]
            sprites=sprites,
            placeholders=placeholders,
            layers=layers,
        )


class SpriteRegistry:
    """Lookup table for manifest sprites keyed by identifier."""

    def __init__(self, manifest: GraphicsManifest) -> None:
        self._manifest = manifest
        self._sprites = dict(manifest.sprites)

    def resolve(self, sprite_id: str) -> ManifestSprite | None:
        return self._sprites.get(sprite_id)

    def texture_path(self, sprite_id: str) -> Path | None:
        sprite = self.resolve(sprite_id)
        return sprite.texture_path if sprite is not None else None

    @property
    def layers(self) -> Mapping[str, LayerDefinition]:
        return self._manifest.layers

    @property
    def placeholders(self) -> Mapping[str, str]:
        return self._manifest.placeholders


def _optional_tint(payload: Any) -> Tuple[int, int, int] | None:
    if payload is None:
        return None

    if isinstance(payload, Mapping):
        r = payload.get("r") or payload.get("red")
        g = payload.get("g") or payload.get("green")
        b = payload.get("b") or payload.get("blue")
        if r is not None and g is not None and b is not None:
            return (int(r), int(g), int(b))

    values = _as_iterable(payload)
    if len(values) >= 3:
        return (int(values[0]), int(values[1]), int(values[2]))
    return None


def _tuple_of_strings(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, Mapping):
        iterable = value.values()
    elif isinstance(value, (str, bytes, bytearray)):
        return (str(value),)
    else:
        iterable = value

    try:
        return tuple(str(entry) for entry in iterable)
    except TypeError:
        return (str(value),)


def _coerce_int_pair(payload: Any, *, default: Tuple[int, int]) -> Tuple[int, int]:
    first, second = _coerce_pair(payload, default=default)
    return int(first), int(second)


def _coerce_float_pair(payload: Any, *, default: Tuple[float, float]) -> Tuple[float, float]:
    first, second = _coerce_pair(payload, default=default)
    return float(first), float(second)


def _coerce_pair(payload: Any, *, default: Tuple[float, float]) -> Tuple[float, float]:
    if isinstance(payload, Mapping):
        first = _first_present(payload, "x", "width", "w")
        second = _first_present(payload, "y", "height", "h")
        return (
            float(default[0]) if first is None else float(first),
            float(default[1]) if second is None else float(second),
        )

    values = _as_iterable(payload)
    if len(values) >= 2:
        return float(values[0]), float(values[1])
    if len(values) == 1:
        single = float(values[0])
        return single, single
    return float(default[0]), float(default[1])


def _first_present(payload: Mapping[str, Any], *keys: str) -> Any | None:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _as_iterable(value: Any) -> Tuple[Any, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _normalise_placeholders(payload: Any) -> Dict[str, str]:
    if isinstance(payload, Mapping):
        return {str(kind): str(sprite_id) for kind, sprite_id in payload.items()}

    placeholders: Dict[str, str] = {}
    for entry in _as_iterable(payload):
        if isinstance(entry, Mapping):
            kind = entry.get("kind") or entry.get("id")
            sprite_id = entry.get("sprite") or entry.get("sprite_id") or entry.get("value")
            if kind is None or sprite_id is None:
                continue
            placeholders[str(kind)] = str(sprite_id)
        elif isinstance(entry, Sequence) and not isinstance(entry, (str, bytes, bytearray)):
            if len(entry) >= 2:
                placeholders[str(entry[0])] = str(entry[1])
    return placeholders


__all__ = [
    "GraphicsManifest",
    "LayerDefinition",
    "ManifestSprite",
    "SpriteRegistry",
]
