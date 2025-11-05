"""Helpers for consuming the graphics manifest in the native client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

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
        for entry in sprites_payload:
            sprite = ManifestSprite(
                id=str(entry["id"]),
                texture=str(entry["texture"]),
                size=(int(entry["size"][0]), int(entry["size"][1])),  # type: ignore[index]
                pivot=(float(entry["pivot"][0]), float(entry["pivot"][1])),  # type: ignore[index]
                tint=_optional_tint(entry.get("tint")),
                display_name=entry.get("display_name") or None,
                role=str(entry.get("role", "")),
                description=str(entry.get("description", "")),
                palette=_tuple_of_strings(entry.get("palette", ())),
                mood=str(entry.get("mood", "")),
                lighting=str(entry.get("lighting", "")),
                art_style=str(entry.get("art_style", "")),
                notes=_tuple_of_strings(entry.get("notes", ())),
                tags=_tuple_of_strings(entry.get("tags", ())),
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

        placeholders = {str(kind): str(sprite_id) for kind, sprite_id in placeholders_payload.items()}

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
    return (int(payload[0]), int(payload[1]), int(payload[2]))  # type: ignore[index]


def _tuple_of_strings(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    return tuple(str(entry) for entry in value)


__all__ = [
    "GraphicsManifest",
    "LayerDefinition",
    "ManifestSprite",
    "SpriteRegistry",
]
